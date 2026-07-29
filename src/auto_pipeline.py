"""Automatic preparation orchestration in front of the validated pipeline."""

from __future__ import annotations

import json
import math
import re
from dataclasses import replace
from pathlib import Path

from .camera_grouping import group_camera_sources
from .edl_generator import calculate_duration_metrics, generate_edl
from .errors import PreparationError
from .evidence import utc_now
from .json_utils import write_generated_json, write_json_atomic
from .models import (
    AutomationOutcome,
    CameraSource,
    DiscoveredVideo,
    DurationPolicy,
    OutputSpec,
    PreparationResult,
    ProjectConfig,
    SyncConfig,
    TextSpec,
)
from .pipeline import PreparedPipeline, prepare_pipeline, render_draft
from .sync import apply_sync
from .sync_assistant import analyse_sync
from .video_discovery import discover_videos

DEFAULT_CREDITS_TEXT = "Edited by the Project Team"


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return cleaned or "kindergarten-graduation"


def _camera_sources(
    group: tuple[DiscoveredVideo, ...],
) -> tuple[CameraSource, ...]:
    cameras: list[CameraSource] = []
    for item in group:
        camera_id = item.camera_id
        if camera_id is None:
            continue
        cameras.append(
            CameraSource(
                id=camera_id,
                path=item.path,
                duration_seconds=item.duration_seconds,
                width=item.width,
                height=item.height,
                fps=item.fps,
                has_audio=item.has_audio,
                video_codec=item.video_codec,
                audio_codec=item.audio_codec,
            )
        )
    return tuple(cameras)


def _project_data(
    *,
    project_root: Path,
    project_name: str,
    master_camera: str,
    cameras: tuple[CameraSource, ...],
    title: str,
    credits: str,
    credits_duration: float | None,
    smoke: bool,
    target_duration: float,
) -> dict[str, object]:
    presentation_duration = 1.0 if smoke else 4.0
    resolved_credits_duration = (
        presentation_duration if credits_duration is None else credits_duration
    )
    policy = (
        {
            "min_seconds": max(0.1, target_duration - 0.25),
            "max_seconds": target_duration + 0.25,
            "includes_title_and_credits": True,
        }
        if smoke
        else {
            "min_seconds": 60.0,
            "max_seconds": 180.0,
            "includes_title_and_credits": True,
        }
    )
    return {
        "project": project_name,
        "master_camera": master_camera,
        "renderer": "moviepy",
        "allow_ffmpeg_fallback": True,
        "output": {
            "width": 1280,
            "height": 720,
            "fps": 30,
            "video_codec": "libx264",
            "audio_codec": "aac",
        },
        "duration_policy": policy,
        "title": {"text": title, "duration": presentation_duration},
        "credits": {
            "text": credits,
            "duration": resolved_credits_duration,
        },
        "cameras": [
            {
                "id": camera.id,
                "path": camera.path.resolve()
                .relative_to(project_root.resolve())
                .as_posix(),
            }
            for camera in cameras
        ],
    }


def _typed_config(
    *,
    project_name: str,
    master_camera: str,
    cameras: tuple[CameraSource, ...],
    title: str,
    credits: str,
    credits_duration: float | None,
    smoke: bool,
    target_duration: float,
) -> ProjectConfig:
    presentation_duration = 1.0 if smoke else 4.0
    resolved_credits_duration = (
        presentation_duration if credits_duration is None else credits_duration
    )
    policy = (
        DurationPolicy(max(0.1, target_duration - 0.25), target_duration + 0.25, True)
        if smoke
        else DurationPolicy(60, 180, True)
    )
    return ProjectConfig(
        project=project_name,
        master_camera=master_camera,
        renderer="moviepy",
        allow_ffmpeg_fallback=True,
        output=OutputSpec(),
        title=TextSpec(title, presentation_duration),
        credits=TextSpec(credits, resolved_credits_duration),
        cameras=cameras,
        duration_policy=policy,
    )


def _summary_payload(
    result: PreparationResult, *, draft_path: Path | None = None
) -> dict[str, object]:
    return {
        "generated_at": utc_now(),
        "outcome": result.outcome.value,
        "discovered_videos": result.discovered_count,
        "usable_camera_candidates": result.usable_camera_count,
        "master_camera": result.master_camera,
        "sync_status": result.sync_status,
        "requested_duration_seconds": result.requested_duration_seconds,
        "common_overlap_duration": result.common_overlap_duration,
        "total_event_coverage": result.total_event_coverage,
        "maximum_renderable_duration": result.maximum_renderable_duration,
        "generated_project": str(result.project_path) if result.project_path else None,
        "generated_sync": str(result.sync_path) if result.sync_path else None,
        "generated_edl": str(result.edl_path) if result.edl_path else None,
        "draft": str(draft_path) if draft_path else None,
        "render_permitted": result.render_permitted,
        "smoke": result.smoke,
        "human_review_required": True,
        "final_approval_performed": False,
        "warnings": list(result.warnings),
        "camera_grouping": {
            "state": result.camera_group_state,
            "best_score": result.camera_group_score,
            "analysed_pair_count": result.analysed_pair_count,
            "selected_paths": list(result.selected_camera_paths),
            "excluded_derived_count": result.excluded_derived_count,
        },
    }


def _is_managed_generated_file(path: Path) -> bool:
    """Recognize prior automation output without treating arbitrary JSON as managed."""
    if not path.is_file() or not path.name.startswith("generated_"):
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(payload, dict):
        return False
    if payload.get("generated_by") in {
        "automatic_preparation_layer",
        "deterministic_rule_based_edl_generator",
    }:
        return True
    if payload.get("acceptance_status") == "needs_human_confirmation" and isinstance(
        payload.get("camera_analyses"), list
    ):
        return True
    project = payload.get("project")
    return isinstance(project, str) and "unverified-sync" in project


def prepare_automatic(
    *,
    project_root: Path,
    input_path: Path,
    requested_duration_seconds: float,
    title: str,
    credits: str = DEFAULT_CREDITS_TEXT,
    credits_duration: float | None = None,
    ffmpeg_executable: str | Path | None = None,
    ffprobe_executable: str | Path | None = None,
    search_window_seconds: float = 15.0,
    alignment_window_seconds: float = 120.0,
    allow_smoke: bool = False,
    include_derived: bool = False,
    overwrite: bool = False,
    camera_files: tuple[Path, ...] = (),
    continue_low_confidence: bool = False,
) -> PreparationResult:
    credits = credits.strip()
    if not credits:
        raise PreparationError("--credits must be a non-empty string.")
    if credits_duration is not None and (
        not math.isfinite(credits_duration) or credits_duration <= 0
    ):
        raise PreparationError("--credits-duration must be a finite number above zero.")
    root = project_root.resolve()
    reports = root / "evidence" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    project_path = root / "config" / "generated_project.json"
    sync_path = root / "config" / "generated_sync.json"
    edl_path = root / "edl" / "generated_editing_decisions.json"
    summary_path = reports / "automatic_preparation.json"
    discovery = discover_videos(
        input_path,
        project_root=root,
        ffprobe_executable=ffprobe_executable,
        include_derived=include_derived,
        report_path=reports / "video_discovery.json",
    )
    grouping_path = reports / "camera_grouping.json"
    grouping = group_camera_sources(
        discovery.videos,
        input_path=input_path,
        ffmpeg_executable=ffmpeg_executable,
        minimum_common_duration_seconds=(
            min(16.0, max(4.0, requested_duration_seconds - 2.0))
            if allow_smoke
            else 8.0
        ),
        explicit_camera_files=camera_files,
        report_path=grouping_path,
    )
    group = grouping.selected_videos
    low_confidence_override = bool(
        continue_low_confidence and grouping.confidence in {"low", "medium"}
    )
    if not group and continue_low_confidence and len(grouping.suggested_videos) >= 2:
        group = grouping.suggested_videos
    if len(group) < 2 or (
        grouping.confidence == "medium"
        and not allow_smoke
        and not camera_files
        and not continue_low_confidence
    ):
        medium_warning = (
            "The best camera group has medium confidence and may be used only for "
            "an explicitly labelled smoke draft."
            if group
            else grouping.reason
        )
        result = PreparationResult(
            outcome=AutomationOutcome.NEEDS_CAMERA_SELECTION,
            discovered_count=len(discovery.videos),
            usable_camera_count=grouping.eligible_count,
            master_camera=None,
            sync_status="NOT_RUN",
            requested_duration_seconds=requested_duration_seconds,
            common_overlap_duration=None,
            total_event_coverage=None,
            maximum_renderable_duration=None,
            project_path=None,
            sync_path=None,
            edl_path=None,
            summary_path=summary_path,
            render_permitted=False,
            smoke=False,
            warnings=(medium_warning,),
            camera_group_state=grouping.state.value,
            camera_group_score=grouping.best_score,
            analysed_pair_count=grouping.analysed_pair_count,
            selected_camera_paths=tuple(
                video.relative_path
                for video in (
                    grouping.suggested_videos
                    if grouping.suggested_videos
                    else grouping.selected_videos
                )
            ),
            excluded_derived_count=grouping.excluded_derived_count,
        )
        write_json_atomic(summary_path, _summary_payload(result))
        return result

    cameras = _camera_sources(group)
    master_camera = cameras[0].id
    managed_overwrite = overwrite or all(
        _is_managed_generated_file(path)
        for path in (project_path, sync_path, edl_path)
        if path.exists()
    )
    analyses, sync_data = analyse_sync(
        cameras,
        master_camera=master_camera,
        search_window_seconds=search_window_seconds,
        alignment_window_seconds=alignment_window_seconds,
        ffmpeg_executable=ffmpeg_executable,
        sync_path=sync_path,
        report_path=reports / "sync_candidates.json",
        overwrite=managed_overwrite,
    )
    complete_sync = all(
        item.selected_timestamp_seconds is not None for item in analyses
    )
    sync_sanity = sync_data.get("sync_sanity")
    sync_sanity_warnings = (
        [str(item) for item in sync_sanity.get("warnings", [])]
        if isinstance(sync_sanity, dict)
        else []
    )
    base_project_name = f"{_slug(title)}-unverified-sync"
    if not complete_sync:
        project_data = _project_data(
            project_root=root,
            project_name=base_project_name,
            master_camera=master_camera,
            cameras=cameras,
            title=title,
            credits=credits,
            credits_duration=credits_duration,
            smoke=False,
            target_duration=requested_duration_seconds,
        )
        project_data["generated_by"] = "automatic_preparation_layer"
        write_generated_json(project_path, project_data, overwrite=managed_overwrite)
        result = PreparationResult(
            outcome=AutomationOutcome.NEEDS_SYNC_CONFIRMATION,
            discovered_count=len(discovery.videos),
            usable_camera_count=grouping.eligible_count,
            master_camera=master_camera,
            sync_status="NEEDS_SYNC_CONFIRMATION",
            requested_duration_seconds=requested_duration_seconds,
            common_overlap_duration=None,
            total_event_coverage=None,
            maximum_renderable_duration=None,
            project_path=project_path,
            sync_path=sync_path,
            edl_path=None,
            summary_path=summary_path,
            render_permitted=False,
            smoke=False,
            warnings=tuple(
                [
                    (
                        "At least one camera has no reliable audio transient. "
                        "Candidate times were saved, but no missing timestamp was "
                        "invented."
                    )
                ]
                + (
                    [
                        (
                            "The low-confidence camera-group suggestion was "
                            "explicitly continued for human verification."
                        )
                    ]
                    if low_confidence_override
                    else []
                )
            ),
            camera_group_state=grouping.state.value,
            camera_group_score=grouping.best_score,
            analysed_pair_count=grouping.analysed_pair_count,
            selected_camera_paths=tuple(video.relative_path for video in group),
            excluded_derived_count=grouping.excluded_derived_count,
        )
        write_json_atomic(summary_path, _summary_payload(result))
        return result

    sync_config = SyncConfig(
        master_camera=master_camera,
        clap_timestamps={
            str(key): float(value)
            for key, value in dict(sync_data["clap_timestamps"]).items()
        },
        verification_threshold_ms=100,
        cue_type="shared_audio_transient",
        cue_description=str(sync_data["cue_description"]),
        acceptance_status="needs_human_confirmation",
    )
    synced_cameras = apply_sync(
        cameras, sync_config, expected_master_camera=master_camera
    )
    standard_config = _typed_config(
        project_name=base_project_name,
        master_camera=master_camera,
        cameras=synced_cameras,
        title=title,
        credits=credits,
        credits_duration=credits_duration,
        smoke=False,
        target_duration=requested_duration_seconds,
    )
    standard_metrics = calculate_duration_metrics(standard_config)
    maximum_standard = standard_metrics.maximum_renderable_duration
    smoke = False
    target_duration = requested_duration_seconds
    if requested_duration_seconds > maximum_standard + 0.001:
        if not allow_smoke:
            project_data = _project_data(
                project_root=root,
                project_name=base_project_name,
                master_camera=master_camera,
                cameras=cameras,
                title=title,
                credits=credits,
                credits_duration=credits_duration,
                smoke=False,
                target_duration=requested_duration_seconds,
            )
            project_data["generated_by"] = "automatic_preparation_layer"
            write_generated_json(
                project_path, project_data, overwrite=managed_overwrite
            )
            result = PreparationResult(
                outcome=AutomationOutcome.INSUFFICIENT_RENDERABLE_DURATION,
                discovered_count=len(discovery.videos),
                usable_camera_count=grouping.eligible_count,
                master_camera=master_camera,
                sync_status="NEEDS_SYNC_CONFIRMATION",
                requested_duration_seconds=requested_duration_seconds,
                common_overlap_duration=standard_metrics.common_overlap_duration,
                total_event_coverage=standard_metrics.total_event_coverage,
                maximum_renderable_duration=maximum_standard,
                project_path=project_path,
                sync_path=sync_path,
                edl_path=None,
                summary_path=summary_path,
                render_permitted=False,
                smoke=False,
                warnings=tuple(
                    [
                        (
                            "The requested duration exceeds the maximum coverage-aware "
                            "renderable duration. No looping, padding, freezing, or "
                            "time stretching was used."
                        )
                    ]
                    + sync_sanity_warnings
                    + (
                        [
                            (
                                "The camera-group suggestion was explicitly "
                                "continued for human verification."
                            )
                        ]
                        if low_confidence_override
                        else []
                    )
                ),
                camera_group_state=grouping.state.value,
                camera_group_score=grouping.best_score,
                analysed_pair_count=grouping.analysed_pair_count,
                selected_camera_paths=tuple(video.relative_path for video in group),
                excluded_derived_count=grouping.excluded_derived_count,
            )
            write_json_atomic(summary_path, _summary_payload(result))
            return result
        smoke = True
        smoke_capacity_config = _typed_config(
            project_name=base_project_name + "-smoke",
            master_camera=master_camera,
            cameras=synced_cameras,
            title=title,
            credits=credits,
            credits_duration=credits_duration,
            smoke=True,
            target_duration=requested_duration_seconds,
        )
        smoke_metrics = calculate_duration_metrics(
            smoke_capacity_config, allow_smoke=True
        )
        target_duration = min(
            requested_duration_seconds,
            smoke_metrics.maximum_renderable_duration,
        )
    elif requested_duration_seconds < 60:
        if not allow_smoke:
            raise PreparationError(
                "Durations below 60 seconds require the explicit --allow-smoke flag."
            )
        smoke = True
    if smoke and target_duration <= 6:
        raise PreparationError(
            "The renderable event coverage is too short even for a four-segment "
            "smoke render."
        )

    project_name = base_project_name + ("-smoke" if smoke else "")
    config = _typed_config(
        project_name=project_name,
        master_camera=master_camera,
        cameras=synced_cameras,
        title=title,
        credits=credits,
        credits_duration=credits_duration,
        smoke=smoke,
        target_duration=target_duration,
    )
    project_data = _project_data(
        project_root=root,
        project_name=project_name,
        master_camera=master_camera,
        cameras=cameras,
        title=title,
        credits=credits,
        credits_duration=credits_duration,
        smoke=smoke,
        target_duration=target_duration,
    )
    project_data["generated_by"] = "automatic_preparation_layer"
    write_generated_json(project_path, project_data, overwrite=managed_overwrite)
    generate_edl(
        config,
        requested_duration_seconds=target_duration,
        allow_smoke=smoke,
        output_path=edl_path,
        report_path=reports / "generated_edl.json",
        overwrite=managed_overwrite,
    )
    # Re-load every serialized artefact through the established validated pipeline.
    prepare_pipeline(
        project_path,
        sync_path,
        edl_path,
        ffprobe_executable=ffprobe_executable,
        write_evidence=False,
    )
    outcome = (
        AutomationOutcome.READY_FOR_SMOKE_ONLY
        if smoke
        else AutomationOutcome.NEEDS_SYNC_CONFIRMATION
    )
    warnings = [
        "Audio transient timestamps are suggestions, not a verified deliberate clap."
    ] + sync_sanity_warnings
    if low_confidence_override:
        warnings.append(
            "The camera group was a low-confidence suggestion explicitly accepted "
            "for human verification; grouping confidence does not verify "
            "synchronization."
        )
    if smoke:
        warnings.append(
            "Smoke output does not satisfy the 60-180 second submission requirement "
            "and is ineligible for final approval."
        )
    duration_metrics = calculate_duration_metrics(config, allow_smoke=smoke)
    result = PreparationResult(
        outcome=outcome,
        discovered_count=len(discovery.videos),
        usable_camera_count=grouping.eligible_count,
        master_camera=master_camera,
        sync_status="NEEDS_SYNC_CONFIRMATION",
        requested_duration_seconds=requested_duration_seconds,
        common_overlap_duration=duration_metrics.common_overlap_duration,
        total_event_coverage=duration_metrics.total_event_coverage,
        maximum_renderable_duration=duration_metrics.maximum_renderable_duration,
        project_path=project_path,
        sync_path=sync_path,
        edl_path=edl_path,
        summary_path=summary_path,
        render_permitted=True,
        smoke=smoke,
        warnings=tuple(warnings),
        camera_group_state=grouping.state.value,
        camera_group_score=grouping.best_score,
        analysed_pair_count=grouping.analysed_pair_count,
        selected_camera_paths=tuple(video.relative_path for video in group),
        excluded_derived_count=grouping.excluded_derived_count,
    )
    write_json_atomic(summary_path, _summary_payload(result))
    return result


def run_automatic(
    **kwargs: object,
) -> tuple[PreparationResult, PreparedPipeline | None, object | None]:
    result = prepare_automatic(**kwargs)  # type: ignore[arg-type]
    if not result.render_permitted:
        return result, None, None
    ffprobe = kwargs.get("ffprobe_executable")
    ffmpeg = kwargs.get("ffmpeg_executable")
    prepared = prepare_pipeline(
        result.project_path,
        result.sync_path,
        result.edl_path,
        ffprobe_executable=ffprobe,
    )
    rendered = render_draft(
        prepared,
        ffmpeg_executable=ffmpeg,
        ffprobe_executable=ffprobe,
    )
    outcome = AutomationOutcome.DRAFT_RENDERED_WITH_UNVERIFIED_SYNC
    rendered_result = replace(result, outcome=outcome)
    write_json_atomic(
        result.summary_path,
        _summary_payload(rendered_result, draft_path=rendered[0].output_path),
    )
    return rendered_result, prepared, rendered
