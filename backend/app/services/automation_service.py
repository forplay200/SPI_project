"""Direct adapters from HTTP workflows to the established pipeline functions."""

from __future__ import annotations

import re
import threading
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from backend.app.schemas.api import JobStatus, ProjectResponse
from backend.app.security.path_policy import PathPolicy
from backend.app.services.job_service import JobContext
from backend.app.services.project_service import ProjectService
from src.camera_grouping import group_camera_sources
from src.edl import parse_edl_data, validate_edl
from src.edl_generator import calculate_duration_metrics, generate_edl
from src.errors import InputFileError
from src.evidence import sha256_file
from src.json_utils import read_json_object, write_json_atomic
from src.media_probe import probe_cameras, probe_video
from src.models import CameraSource, DiscoveredVideo
from src.pipeline import prepare_pipeline, render_draft
from src.render_plan import build_render_plan
from src.review import (
    REVIEW_CHECKLIST_ITEMS,
    load_review_record,
    promote_approved_draft,
    record_review,
)
from src.sync import apply_sync, load_sync_config
from src.sync_assistant import analyse_sync, confirm_sync_timestamp
from src.validate_inputs import load_project_config
from src.video_discovery import discover_videos


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    return cleaned or "kindergarten-graduation"


class AutomationService:
    """Compose UI operations from existing, independently validated functions."""

    def __init__(self, project_root: Path, projects: ProjectService) -> None:
        self.project_root = project_root.resolve()
        self.projects = projects
        self.path_policy = PathPolicy(self.project_root)
        self._pipeline_lock = threading.RLock()

    def _project_paths(self, project_id: str) -> dict[str, Path]:
        safe = re.sub(r"[^A-Za-z0-9_-]", "-", project_id)
        report_root = self.project_root / "evidence" / "ui" / safe
        report_root.mkdir(parents=True, exist_ok=True)
        return {
            "discovery": report_root / "video_discovery.json",
            "grouping": report_root / "camera_grouping.json",
            "selection": report_root / "camera_selection.json",
            "sync_report": report_root / "sync_candidates.json",
            "edl_report": report_root / "generated_edl.json",
            "project": self.project_root / "config" / f"{safe}_project.json",
            "sync": self.project_root / "config" / f"{safe}_sync.json",
            "edl": self.project_root / "edl" / f"{safe}_editing_decisions.json",
            "review": self.project_root
            / "evidence"
            / "approvals"
            / f"{safe}_review.json",
        }

    def _store_artifacts(self, project_id: str, paths: dict[str, Path]) -> None:
        project = self.projects.get(project_id)
        artifacts = dict(project.artifacts)
        for key, path in paths.items():
            if path.exists():
                artifacts[key] = str(path.resolve())
        self.projects.patch(project_id, artifacts=artifacts)

    def _duration_fields(self, project_id: str) -> dict[str, float | None]:
        metrics = self.projects.runtime(project_id, "duration_metrics")
        return {
            "common_overlap_duration": (
                metrics.common_overlap_duration if metrics is not None else None
            ),
            "total_event_coverage": (
                metrics.total_event_coverage if metrics is not None else None
            ),
            "maximum_renderable_duration": (
                metrics.maximum_renderable_duration if metrics is not None else None
            ),
        }

    def analyse(self, project_id: str, context: JobContext) -> dict[str, Any]:
        project = self.projects.get(project_id)
        input_path = self.path_policy.resolve_input_directory(project.input_folder)
        paths = self._project_paths(project_id)
        context.update(
            JobStatus.DISCOVERING, 10, "Discovering local videos", current_step=2
        )
        context.update(
            JobStatus.PROBING_MEDIA,
            25,
            "Reading stream metadata with FFprobe",
            current_step=2,
        )
        discovery = discover_videos(
            input_path,
            project_root=self.project_root,
            report_path=paths["discovery"],
        )
        context.update(
            JobStatus.GROUPING_CAMERAS,
            55,
            f"Comparing {len(discovery.usable_videos)} eligible camera candidates",
            current_step=2,
        )
        grouping = group_camera_sources(
            discovery.videos,
            input_path=input_path,
            minimum_common_duration_seconds=(
                min(16.0, max(4.0, project.duration_seconds - 2.0))
                if project.smoke_mode
                else 8.0
            ),
            report_path=paths["grouping"],
        )
        self.projects.set_runtime(project_id, "discovery", discovery)
        self.projects.set_runtime(project_id, "grouping", grouping)
        self._store_artifacts(project_id, paths)
        selected = [item.camera_id for item in grouping.selected_videos]
        suggested = [item.camera_id for item in grouping.suggested_videos]
        outcome = (
            "NEEDS_CAMERA_SELECTION"
            if len(selected) < 2
            else (
                "READY_FOR_SMOKE_ONLY"
                if grouping.confidence == "medium"
                else "NEEDS_SYNC_CONFIRMATION"
            )
        )
        self.projects.patch(project_id, outcome=outcome, current_step=2)
        return {
            "discovered_videos": len(discovery.videos),
            "usable_camera_candidates": len(discovery.usable_videos),
            "excluded_outputs": sum(
                item.classification == "likely_derived_output"
                for item in discovery.videos
            ),
            "videos": [_jsonable(asdict(item)) for item in discovery.videos],
            "grouping": {
                **_jsonable(asdict(grouping)),
                "state": grouping.state.value,
            },
            "selected_camera_ids": selected,
            "master_camera": selected[0] if selected else None,
            "suggested_camera_ids": suggested,
            "suggested_master_camera": suggested[0] if suggested else None,
            "outcome": outcome,
            **self._duration_fields(project_id),
        }

    def get_analysis(self, project_id: str) -> dict[str, Any] | None:
        grouping = self.projects.runtime(project_id, "grouping")
        discovery = self.projects.runtime(project_id, "discovery")
        if grouping is not None and discovery is not None:
            return {
                "videos": [_jsonable(asdict(item)) for item in discovery.videos],
                "grouping": {
                    **_jsonable(asdict(grouping)),
                    "state": grouping.state.value,
                },
                "selected_camera_ids": [
                    item.camera_id for item in grouping.selected_videos
                ],
                "master_camera": (
                    grouping.selected_videos[0].camera_id
                    if grouping.selected_videos
                    else None
                ),
                "suggested_camera_ids": [
                    item.camera_id for item in grouping.suggested_videos
                ],
                "suggested_master_camera": (
                    grouping.suggested_videos[0].camera_id
                    if grouping.suggested_videos
                    else None
                ),
                **self._duration_fields(project_id),
            }
        paths = self._project_paths(project_id)
        if paths["grouping"].is_file() and paths["discovery"].is_file():
            grouping_payload = read_json_object(
                paths["grouping"], label="Camera grouping report"
            )
            discovery_payload = read_json_object(
                paths["discovery"], label="Video discovery report"
            )
            selection_payload = (
                read_json_object(paths["selection"], label="Camera selection")
                if paths["selection"].is_file()
                else {}
            )
            selected_ids = selection_payload.get(
                "selected_camera_ids", grouping_payload.get("selected_camera_ids", [])
            )
            master = selection_payload.get(
                "master_camera", selected_ids[0] if selected_ids else None
            )
            duration_payload = grouping_payload.get("duration_metrics", {})
            return {
                "videos": discovery_payload.get("videos", []),
                "grouping": {
                    **grouping_payload,
                    "pair_scores": grouping_payload.get("pairs", []),
                },
                "selected_camera_ids": selected_ids,
                "master_camera": master,
                "suggested_camera_ids": grouping_payload.get(
                    "suggested_camera_ids", []
                ),
                "suggested_master_camera": (
                    grouping_payload.get("suggested_camera_ids", [None])[0]
                    if grouping_payload.get("suggested_camera_ids")
                    else None
                ),
                "common_overlap_duration": duration_payload.get(
                    "common_overlap_duration"
                ),
                "total_event_coverage": duration_payload.get("total_event_coverage"),
                "maximum_renderable_duration": duration_payload.get(
                    "maximum_renderable_duration"
                ),
            }
        return None

    def select_camera_group(
        self,
        project_id: str,
        camera_ids: list[str],
        master_camera: str,
        *,
        continue_with_human_verification: bool = False,
    ) -> dict[str, Any]:
        discovery = self.projects.runtime(project_id, "discovery")
        if discovery is None:
            raise ValueError("Run footage analysis before selecting cameras.")
        available = {
            item.camera_id: item
            for item in discovery.videos
            if item.usable and item.camera_id is not None
        }
        missing = sorted(set(camera_ids) - set(available))
        if missing:
            raise ValueError(f"Unknown or unusable cameras: {missing}")
        if master_camera not in camera_ids:
            raise ValueError("The master camera must be in the selected camera group.")
        selected = [available[master_camera]] + [
            available[item] for item in camera_ids if item != master_camera
        ]
        self.projects.set_runtime(project_id, "selected_videos", tuple(selected))
        selection_path = self._project_paths(project_id)["selection"]
        write_json_atomic(
            selection_path,
            {
                "selection_method": (
                    "human_confirmed_same_event_group"
                    if continue_with_human_verification
                    else "human_selected_from_probed_candidates"
                ),
                "selected_camera_ids": [item.camera_id for item in selected],
                "master_camera": master_camera,
                "grouping_confidence_override": continue_with_human_verification,
                "requires_downstream_validation": True,
            },
        )
        self._store_artifacts(project_id, {"selection": selection_path})
        self.projects.patch(
            project_id, outcome="NEEDS_SYNC_CONFIRMATION", current_step=2
        )
        return {
            "selected_camera_ids": [item.camera_id for item in selected],
            "master_camera": master_camera,
            "selection_method": (
                "human_confirmed_same_event_group"
                if continue_with_human_verification
                else "human_selected_from_probed_candidates"
            ),
            "grouping_confidence_override": continue_with_human_verification,
        }

    def _selected_videos(self, project_id: str) -> tuple[DiscoveredVideo, ...]:
        explicit = self.projects.runtime(project_id, "selected_videos")
        if explicit:
            return tuple(explicit)
        grouping = self.projects.runtime(project_id, "grouping")
        if grouping and len(grouping.selected_videos) >= 2:
            return grouping.selected_videos
        paths = self._project_paths(project_id)
        if paths["discovery"].is_file() and paths["grouping"].is_file():
            discovery_payload = read_json_object(
                paths["discovery"], label="Video discovery report"
            )
            grouping_payload = read_json_object(
                paths["grouping"], label="Camera grouping report"
            )
            selection_payload = (
                read_json_object(paths["selection"], label="Camera selection")
                if paths["selection"].is_file()
                else {}
            )
            selected_ids = selection_payload.get(
                "selected_camera_ids", grouping_payload.get("selected_camera_ids", [])
            )
            raw_videos = discovery_payload.get("videos", [])
            if isinstance(selected_ids, list) and isinstance(raw_videos, list):
                by_id = {
                    item.get("camera_id"): item
                    for item in raw_videos
                    if isinstance(item, dict) and item.get("camera_id")
                }
                restored = tuple(
                    self._restore_discovered_video(by_id[camera_id])
                    for camera_id in selected_ids
                    if camera_id in by_id
                )
                if len(restored) >= 2:
                    return restored
        raise ValueError("No supported multi-camera group is currently selected.")

    def _restore_discovered_video(self, payload: dict[str, Any]) -> DiscoveredVideo:
        return DiscoveredVideo(
            camera_id=payload.get("camera_id"),
            path=(self.project_root / str(payload["relative_path"])).resolve(),
            relative_path=str(payload["relative_path"]),
            duration_seconds=payload.get("duration_seconds"),
            width=payload.get("width"),
            height=payload.get("height"),
            display_rotation=int(payload.get("display_rotation", 0)),
            fps=payload.get("fps"),
            video_codec=payload.get("video_codec"),
            has_audio=payload.get("has_audio"),
            audio_codec=payload.get("audio_codec"),
            classification=str(payload.get("classification", "likely_source")),
            usable=bool(payload.get("usable")),
            warnings=tuple(payload.get("warnings") or ()),
            creation_time=payload.get("creation_time"),
        )

    @staticmethod
    def _camera_sources(
        videos: tuple[DiscoveredVideo, ...],
    ) -> tuple[CameraSource, ...]:
        return tuple(
            CameraSource(
                id=str(item.camera_id),
                path=item.path,
                duration_seconds=item.duration_seconds,
                width=item.width,
                height=item.height,
                fps=item.fps,
                has_audio=item.has_audio,
                video_codec=item.video_codec,
                audio_codec=item.audio_codec,
            )
            for item in videos
            if item.camera_id is not None
        )

    def detect_sync(self, project_id: str, context: JobContext) -> dict[str, Any]:
        project = self.projects.get(project_id)
        videos = self._selected_videos(project_id)
        cameras = self._camera_sources(videos)
        master = cameras[0].id
        paths = self._project_paths(project_id)
        context.update(
            JobStatus.ANALYSING_AUDIO,
            30,
            f"Analysing local audio cues for {len(cameras)} cameras",
            current_step=3,
        )
        analyses, payload = analyse_sync(
            cameras,
            master_camera=master,
            search_window_seconds=15.0,
            alignment_window_seconds=120.0,
            sync_path=paths["sync"],
            report_path=paths["sync_report"],
            overwrite=True,
        )
        self.projects.set_runtime(project_id, "sync_analyses", analyses)
        self._write_project_config(project, cameras, paths["project"], payload)
        timestamps = payload.get("clap_timestamps")
        if isinstance(timestamps, dict) and set(timestamps) == {
            camera.id for camera in cameras
        }:
            sync = load_sync_config(paths["sync"])
            synced = apply_sync(cameras, sync, expected_master_camera=cameras[0].id)
            config = replace(load_project_config(paths["project"]), cameras=synced)
            metrics = calculate_duration_metrics(config, allow_smoke=project.smoke_mode)
            self.projects.set_runtime(project_id, "duration_metrics", metrics)
            metric_payload = {
                "common_overlap_duration": metrics.common_overlap_duration,
                "total_event_coverage": metrics.total_event_coverage,
                "maximum_renderable_duration": metrics.maximum_renderable_duration,
            }
            payload["duration_metrics"] = metric_payload
            write_json_atomic(paths["sync"], payload)
            grouping_path = paths["grouping"]
            if grouping_path.is_file():
                grouping_payload = read_json_object(
                    grouping_path, label="Camera grouping report"
                )
                grouping_payload["duration_metrics"] = metric_payload
                write_json_atomic(grouping_path, grouping_payload)
        self._store_artifacts(project_id, paths)
        self.projects.patch(
            project_id, outcome="NEEDS_SYNC_CONFIRMATION", current_step=3
        )
        return {
            **_jsonable(payload),
            "project_path": str(paths["project"]),
            "sync_path": str(paths["sync"]),
        }

    def get_sync(self, project_id: str) -> dict[str, Any] | None:
        path = self._project_paths(project_id)["sync"]
        return (
            read_json_object(path, label="Synchronisation suggestions")
            if path.is_file()
            else None
        )

    def confirm_sync(
        self,
        project_id: str,
        camera_id: str,
        timestamp_seconds: float,
        *,
        acknowledge_sync_risk: bool = False,
    ) -> dict[str, Any]:
        path = self._project_paths(project_id)["sync"]
        cameras = self._camera_sources(self._selected_videos(project_id))
        payload = confirm_sync_timestamp(
            path,
            camera_id=camera_id,
            timestamp_seconds=timestamp_seconds,
            cameras=cameras,
            acknowledge_risk=acknowledge_sync_risk,
        )
        timestamps = payload.get("clap_timestamps")
        if isinstance(timestamps, dict) and set(timestamps) == {
            camera.id for camera in cameras
        }:
            paths = self._project_paths(project_id)
            sync = load_sync_config(path)
            synced = apply_sync(cameras, sync, expected_master_camera=cameras[0].id)
            config = replace(load_project_config(paths["project"]), cameras=synced)
            project = self.projects.get(project_id)
            metrics = calculate_duration_metrics(config, allow_smoke=project.smoke_mode)
            self.projects.set_runtime(project_id, "duration_metrics", metrics)
            payload["duration_metrics"] = {
                "common_overlap_duration": metrics.common_overlap_duration,
                "total_event_coverage": metrics.total_event_coverage,
                "maximum_renderable_duration": metrics.maximum_renderable_duration,
            }
            write_json_atomic(path, payload)
        if payload.get("acceptance_status") == "verified":
            self.projects.patch(project_id, outcome="READY_FOR_DRAFT")
        return _jsonable(payload)

    def reject_sync(
        self,
        project_id: str,
        camera_id: str,
        timestamp_seconds: float | None,
        reason: str,
    ) -> dict[str, Any]:
        path = self._project_paths(project_id)["sync"]
        payload = read_json_object(path, label="Synchronisation suggestions")
        analyses = payload.get("camera_analyses")
        found = False
        if isinstance(analyses, list):
            for item in analyses:
                if isinstance(item, dict) and item.get("camera_id") == camera_id:
                    item["state"] = "rejected_candidate"
                    item["selected_timestamp_seconds"] = None
                    item["requires_human_verification"] = True
                    warnings = list(item.get("warnings") or [])
                    warnings.append(reason.strip())
                    item["warnings"] = warnings
                    found = True
        if not found:
            raise ValueError(f"Camera {camera_id!r} is not in the sync report.")
        timestamps = payload.get("clap_timestamps")
        if isinstance(timestamps, dict) and (
            timestamp_seconds is None or timestamps.get(camera_id) == timestamp_seconds
        ):
            timestamps.pop(camera_id, None)
        confirmations = payload.get("manual_confirmations")
        if isinstance(confirmations, dict):
            confirmations.pop(camera_id, None)
        payload["acceptance_status"] = "needs_human_confirmation"
        payload["requires_human_verification"] = True
        payload.pop("duration_metrics", None)
        write_json_atomic(path, payload)
        self.projects.set_runtime(project_id, "duration_metrics", None)
        self.projects.patch(project_id, outcome="NEEDS_SYNC_CONFIRMATION")
        return _jsonable(payload)

    def _write_project_config(
        self,
        project: ProjectResponse,
        cameras: tuple[CameraSource, ...],
        path: Path,
        sync_payload: dict[str, Any],
    ) -> None:
        verified = sync_payload.get("acceptance_status") == "verified"
        project_name = _slug(project.title)
        if not verified:
            project_name += "-unverified-sync"
        if project.smoke_mode:
            project_name += "-smoke"
        title_duration = 1.0 if project.smoke_mode else 4.0
        credits_duration = (
            project.credits_duration
            if project.credits_duration is not None
            else (1.0 if project.smoke_mode else 4.0)
        )
        width, height = (int(value) for value in project.resolution.split("x"))
        policy = (
            {
                "min_seconds": max(0.1, project.duration_seconds - 0.25),
                "max_seconds": project.duration_seconds + 0.25,
                "includes_title_and_credits": True,
            }
            if project.smoke_mode
            else {
                "min_seconds": 60.0,
                "max_seconds": 180.0,
                "includes_title_and_credits": True,
            }
        )
        write_json_atomic(
            path,
            {
                "generated_by": "guided_automation_workflow_ui",
                "project": project_name,
                "master_camera": cameras[0].id,
                "renderer": "moviepy",
                "allow_ffmpeg_fallback": True,
                "output": {
                    "width": width,
                    "height": height,
                    "fps": 30,
                    "video_codec": "libx264",
                    "audio_codec": "aac",
                },
                "duration_policy": policy,
                "title": {"text": project.title, "duration": title_duration},
                "credits": {"text": project.credits, "duration": credits_duration},
                "cameras": [
                    {"id": camera.id, "path": str(camera.path.resolve())}
                    for camera in cameras
                ],
            },
        )

    def generate_edl(self, project_id: str, context: JobContext) -> dict[str, Any]:
        project = self.projects.get(project_id)
        paths = self._project_paths(project_id)
        if not paths["sync"].is_file():
            raise ValueError("Run synchronisation analysis before generating an EDL.")
        videos = self._selected_videos(project_id)
        cameras = self._camera_sources(videos)
        sync_payload = read_json_object(paths["sync"], label="Synchronisation")
        self._write_project_config(project, cameras, paths["project"], sync_payload)
        context.update(
            JobStatus.GENERATING_EDL,
            30,
            "Applying deterministic camera-rotation rules",
            current_step=4,
        )
        config = load_project_config(paths["project"])
        probed = probe_cameras(config.cameras)
        sync = load_sync_config(paths["sync"])
        synced = apply_sync(probed, sync, expected_master_camera=config.master_camera)
        config = replace(config, cameras=synced)
        edl, metadata = generate_edl(
            config,
            requested_duration_seconds=project.duration_seconds,
            allow_smoke=project.smoke_mode,
            output_path=paths["edl"],
            report_path=paths["edl_report"],
            overwrite=True,
        )
        metrics = calculate_duration_metrics(config, allow_smoke=project.smoke_mode)
        self.projects.set_runtime(project_id, "duration_metrics", metrics)
        context.update(
            JobStatus.VALIDATING,
            75,
            "Validating generated configuration, sync, and EDL",
            current_step=4,
        )
        prepared = prepare_pipeline(
            paths["project"], paths["sync"], paths["edl"], write_evidence=False
        )
        self.projects.set_runtime(project_id, "prepared", prepared)
        self._store_artifacts(project_id, paths)
        outcome = (
            "READY_FOR_SMOKE_ONLY"
            if project.smoke_mode
            else (
                "READY_FOR_DRAFT"
                if sync.acceptance_status == "verified"
                else "NEEDS_SYNC_CONFIRMATION"
            )
        )
        self.projects.patch(project_id, outcome=outcome, current_step=4)
        return {
            "edl": _jsonable(asdict(edl)),
            "metadata": _jsonable(metadata),
            "render_plan": _jsonable(asdict(prepared.plan)),
            "validation": {"valid": True, "errors": []},
        }

    def get_edl(self, project_id: str) -> dict[str, Any] | None:
        path = self._project_paths(project_id)["edl"]
        if not path.is_file():
            return None
        payload = read_json_object(path, label="EDL")
        duration_fields = self._duration_fields(project_id)
        if (
            duration_fields["maximum_renderable_duration"] is None
            and self._project_paths(project_id)["edl_report"].is_file()
        ):
            report = read_json_object(
                self._project_paths(project_id)["edl_report"],
                label="EDL generation report",
            )
            duration_fields = {
                key: report.get(key)
                for key in (
                    "common_overlap_duration",
                    "total_event_coverage",
                    "maximum_renderable_duration",
                )
            }
        payload.update(duration_fields)
        return payload

    def update_edl(self, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        paths = self._project_paths(project_id)
        config = load_project_config(paths["project"])
        probed = probe_cameras(config.cameras)
        sync = load_sync_config(paths["sync"])
        config = replace(
            config,
            cameras=apply_sync(
                probed, sync, expected_master_camera=config.master_camera
            ),
        )
        edl = parse_edl_data(payload)
        validate_edl(edl, config)
        build_render_plan(config, edl)
        write_json_atomic(paths["edl"], payload)
        self.projects.set_runtime(project_id, "prepared", None)
        return {"valid": True, "errors": [], "edl": payload}

    def validate_edl(self, project_id: str) -> dict[str, Any]:
        paths = self._project_paths(project_id)
        prepared = prepare_pipeline(
            paths["project"], paths["sync"], paths["edl"], write_evidence=False
        )
        self.projects.set_runtime(project_id, "prepared", prepared)
        return {
            "valid": True,
            "errors": [],
            "expected_duration_seconds": prepared.plan.expected_duration_seconds,
            "camera_switch_count": prepared.plan.switch_count,
        }

    def render(self, project_id: str, context: JobContext) -> dict[str, Any]:
        paths = self._project_paths(project_id)
        context.update(
            JobStatus.VALIDATING,
            10,
            "Validating the reviewed editing plan",
            current_step=5,
        )
        prepared = prepare_pipeline(paths["project"], paths["sync"], paths["edl"])
        context.update(
            JobStatus.RENDERING,
            35,
            "Rendering a local draft; no approval will be performed",
            current_step=5,
        )
        with self._pipeline_lock:
            result, metadata, evidence = render_draft(prepared)
        context.update(
            JobStatus.VALIDATING_OUTPUT,
            85,
            "Rendered MP4 passed stream and duration validation",
            current_step=5,
        )
        context.update(
            JobStatus.GENERATING_EVIDENCE,
            95,
            "Registering render evidence and checksum",
            current_step=5,
        )
        self.projects.set_runtime(project_id, "draft", result.output_path)
        self.projects.set_runtime(project_id, "render_metadata", metadata)
        project = self.projects.get(project_id)
        artifacts = dict(project.artifacts)
        artifacts.update(
            {
                "draft": str(result.output_path.resolve()),
                "render_evidence": str(evidence.resolve()),
            }
        )
        outcome = (
            "DRAFT_RENDERED_WITH_UNVERIFIED_SYNC"
            if prepared.sync.acceptance_status != "verified" or project.smoke_mode
            else "DRAFT_RENDERED"
        )
        self.projects.patch(
            project_id, artifacts=artifacts, outcome=outcome, current_step=5
        )
        return {
            "draft_path": str(result.output_path.resolve()),
            "renderer_used": result.backend,
            "fallback_reason": result.fallback_reason,
            "metadata": _jsonable(asdict(metadata)),
            "evidence_path": str(evidence.resolve()),
            "sha256": sha256_file(result.output_path),
            "outcome": outcome,
            "human_review_required": True,
            "final_approval_performed": False,
        }

    def draft_details(self, project_id: str) -> dict[str, Any] | None:
        project = self.projects.get(project_id)
        raw = project.artifacts.get("draft")
        if not raw or not Path(raw).is_file():
            return None
        draft = Path(raw)
        metadata = probe_video(draft)
        evidence_path = project.artifacts.get("render_evidence")
        evidence = (
            read_json_object(Path(evidence_path), label="Render evidence")
            if evidence_path and Path(evidence_path).is_file()
            else {}
        )
        return {
            "path": str(draft),
            "filename": draft.name,
            "sha256": sha256_file(draft),
            "metadata": _jsonable(asdict(metadata)),
            "renderer_used": evidence.get("renderer_used"),
            "sync_state": evidence.get("synchronisation", {}).get("acceptance_status"),
            "compliance_state": (
                "SMOKE_NON_COMPLIANT" if project.smoke_mode else "DURATION_VALIDATED"
            ),
            "human_review_required": True,
            **evidence.get("duration_metrics", self._duration_fields(project_id)),
        }

    def record_review(
        self,
        project_id: str,
        *,
        reviewer: str,
        comments: str,
        decision: str,
        checklist: dict[str, bool],
    ) -> dict[str, Any]:
        project = self.projects.get(project_id)
        draft_value = project.artifacts.get("draft")
        if not draft_value:
            raise ValueError("Render a draft before recording human review.")
        path = self._project_paths(project_id)["review"]
        record = record_review(
            project=project.title,
            draft_path=Path(draft_value),
            reviewer=reviewer,
            decision=decision,
            comments=comments,
            checklist=checklist,
            record_path=path,
        )
        artifacts = dict(project.artifacts)
        artifacts["review"] = str(path.resolve())
        outcome = "READY_FOR_APPROVAL" if decision == "approved" else "CHANGES_REQUIRED"
        self.projects.patch(project_id, artifacts=artifacts, outcome=outcome)
        return _jsonable(asdict(record))

    def review(self, project_id: str) -> dict[str, Any]:
        project = self.projects.get(project_id)
        path_value = project.artifacts.get("review")
        if path_value and Path(path_value).is_file():
            return _jsonable(asdict(load_review_record(Path(path_value))))
        return {
            "decision": "not_recorded",
            "checklist": {item: False for item in REVIEW_CHECKLIST_ITEMS},
            "reviewer": "",
            "comments": "",
        }

    def approval_eligibility(self, project_id: str) -> dict[str, Any]:
        project = self.projects.get(project_id)
        blockers: list[str] = []
        draft_value = project.artifacts.get("draft")
        review_value = project.artifacts.get("review")
        sync = self.get_sync(project_id) or {}
        draft = Path(draft_value) if draft_value else None
        if draft is None or not draft.is_file():
            blockers.append("A validated draft has not been rendered.")
        if project.smoke_mode:
            blockers.append("Smoke drafts do not satisfy the 60-180 second policy.")
        if sync.get("acceptance_status") != "verified":
            blockers.append("Synchronisation has not been manually verified.")
        review_status = "not_recorded"
        compliance_status = "not_validated"
        if draft and draft.is_file():
            config_value = project.artifacts.get("project")
            if config_value and Path(config_value).is_file():
                config = load_project_config(
                    Path(config_value), require_camera_files=False
                )
                metadata = probe_video(draft)
                contractual_duration = metadata.duration_seconds
                if not config.duration_policy.includes_title_and_credits:
                    contractual_duration -= (
                        config.title.duration + config.credits.duration
                    )
                duration_valid = (
                    config.duration_policy.min_seconds
                    <= contractual_duration
                    <= config.duration_policy.max_seconds
                )
                compliance_status = (
                    "duration_valid" if duration_valid else "invalid_duration"
                )
                if not duration_valid:
                    blockers.append(
                        "The rendered duration is outside the configured policy."
                    )
            else:
                blockers.append(
                    "The generated project configuration is unavailable for duration validation."
                )
        if not review_value or not Path(review_value).is_file():
            blockers.append("A complete human review has not been recorded.")
        else:
            record = load_review_record(Path(review_value))
            review_status = record.decision
            if record.decision != "approved":
                blockers.append("The latest human review requested changes.")
            elif not all(record.checklist.values()):
                blockers.append("The review checklist is incomplete.")
            if draft and draft.is_file() and record.draft_sha256 != sha256_file(draft):
                blockers.append(
                    "The draft checksum changed after review; a new review is required."
                )
        if draft and any(
            marker in draft.stem.casefold() for marker in ("smoke", "unverified-sync")
        ):
            blockers.append("The draft filename marks it as approval-ineligible.")
        return {
            "eligible": not blockers,
            "blockers": blockers,
            "draft_sha256": sha256_file(draft) if draft and draft.is_file() else None,
            "review_status": review_status,
            "sync_status": str(sync.get("acceptance_status", "not_available")),
            "compliance_status": "smoke" if project.smoke_mode else compliance_status,
        }

    def approve(self, project_id: str) -> dict[str, Any]:
        eligibility = self.approval_eligibility(project_id)
        if not eligibility["eligible"]:
            raise ValueError(
                "Approval is blocked: " + "; ".join(eligibility["blockers"])
            )
        project = self.projects.get(project_id)
        final = promote_approved_draft(
            draft_path=Path(project.artifacts["draft"]),
            review_record_path=Path(project.artifacts["review"]),
            final_directory=self.project_root / "output" / "final",
        )
        artifacts = dict(project.artifacts)
        artifacts["final"] = str(final.resolve())
        self.projects.patch(
            project_id, artifacts=artifacts, outcome="APPROVED", current_step=6
        )
        return {
            "status": "APPROVED",
            "final_path": str(final.resolve()),
            "sha256": sha256_file(final),
            "rerendered": False,
        }

    def evidence_items(self, project_id: str) -> list[dict[str, Any]]:
        project = self.projects.get(project_id)
        labels = {
            "discovery": ("Footage inventory", "inventory"),
            "grouping": ("Camera grouping", "camera_grouping"),
            "selection": ("Camera selection", "camera_grouping"),
            "sync_report": ("Synchronisation report", "synchronisation"),
            "sync": ("Generated sync configuration", "synchronisation"),
            "project": ("Generated project configuration", "configuration"),
            "edl": ("Generated editing decisions", "editing_plan"),
            "edl_report": ("EDL generation report", "editing_plan"),
            "render_evidence": ("Render report", "render"),
            "review": ("Human review record", "review"),
            "final": ("Approval output", "approval"),
        }
        result = []
        for key, raw in sorted(project.artifacts.items()):
            path = Path(raw)
            try:
                safe_path = self.path_policy.require_registered_file(path, {path})
            except InputFileError:
                safe_path = None
            label, category = labels.get(key, (key.replace("_", " ").title(), "other"))
            result.append(
                {
                    "id": key,
                    "label": label,
                    "category": category,
                    "path": str(safe_path) if safe_path else "",
                    "media_type": (
                        "application/json"
                        if safe_path and safe_path.suffix == ".json"
                        else "video/mp4"
                    ),
                    "exists": safe_path is not None,
                }
            )
        return result

    def registered_files(self, project_id: str) -> dict[str, Path]:
        project = self.projects.get(project_id)
        files = {key: Path(path) for key, path in project.artifacts.items()}
        try:
            files.update(
                {
                    f"camera-{item.camera_id}": item.path
                    for item in self._selected_videos(project_id)
                }
            )
        except ValueError:
            pass
        return files

    def evidence_payload(self, project_id: str, evidence_id: str) -> dict[str, Any]:
        files = self.registered_files(project_id)
        path = files.get(evidence_id)
        if path is None:
            raise FileNotFoundError(evidence_id)
        try:
            path = self.path_policy.require_registered_file(path, set(files.values()))
        except InputFileError as exc:
            raise FileNotFoundError(evidence_id) from exc
        if path.suffix.casefold() != ".json":
            raise FileNotFoundError(evidence_id)
        return read_json_object(path, label="Evidence")
