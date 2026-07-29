"""Machine-readable local evidence and checksums."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .json_utils import write_json_atomic
from .models import (
    EDL,
    CameraSource,
    DurationMetrics,
    MediaMetadata,
    RenderPlan,
    RenderResult,
    SyncConfig,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _shared_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.name


def write_preflight_evidence(
    path: Path,
    *,
    project_root: Path,
    cameras: Iterable[CameraSource],
    edl: EDL,
    plan: RenderPlan,
    sync_config: SyncConfig,
    duration_metrics: DurationMetrics,
) -> None:
    camera_items = []
    for camera in cameras:
        camera_items.append(
            {
                "id": camera.id,
                "path": _shared_path(camera.path, project_root),
                "duration_seconds": camera.duration_seconds,
                "width": camera.width,
                "height": camera.height,
                "fps": camera.fps,
                "has_audio": camera.has_audio,
                "video_codec": camera.video_codec,
                "audio_codec": camera.audio_codec,
                "synchronization_cue_time_seconds": camera.clap_time_seconds,
                "clap_time_seconds": (
                    camera.clap_time_seconds
                    if sync_config.cue_type == "manual_clap"
                    else None
                ),
                "offset_seconds": camera.offset_seconds,
            }
        )
    write_json_atomic(
        path,
        {
            "generated_at": utc_now(),
            "project": plan.project,
            "processing": "local-only deterministic EDL pipeline",
            "cameras": camera_items,
            "synchronisation": {
                "camera_offsets_seconds": plan.camera_offsets,
                "cue_type": sync_config.cue_type,
                "cue_description": sync_config.cue_description,
                "acceptance_status": sync_config.acceptance_status,
                "verification_threshold_ms": sync_config.verification_threshold_ms,
                "clock_drift_correction": False,
            },
            "edl": {
                "segment_count": len(edl.timeline),
                "camera_switch_count": edl.switch_count,
                "main_duration_seconds": edl.main_duration_seconds,
                "reasons": [
                    {
                        "segment_id": item.id,
                        "camera": item.camera,
                        "reason": item.reason,
                    }
                    for item in edl.timeline
                ],
            },
            "duration_metrics": {
                "common_overlap_duration": duration_metrics.common_overlap_duration,
                "total_event_coverage": duration_metrics.total_event_coverage,
                "maximum_renderable_duration": (
                    duration_metrics.maximum_renderable_duration
                ),
                "presentation_duration": duration_metrics.presentation_duration,
            },
            "render_plan": {
                "expected_output_duration_seconds": plan.expected_duration_seconds,
                "output": asdict(plan.output),
                "renderer_requested": plan.renderer,
            },
        },
    )


def write_render_evidence(
    path: Path,
    *,
    project_root: Path,
    result: RenderResult,
    output_metadata: MediaMetadata,
    plan: RenderPlan,
    sync_config: SyncConfig,
    duration_metrics: DurationMetrics,
    warnings: Iterable[str] = (),
) -> None:
    all_warnings = list(result.warnings) + list(warnings)
    write_json_atomic(
        path,
        {
            "generated_at": utc_now(),
            "project": plan.project,
            "output_path": _shared_path(result.output_path, project_root),
            "output_sha256": sha256_file(result.output_path),
            "renderer_requested": plan.renderer,
            "renderer_used": result.backend,
            "fallback_activated": result.fallback_reason is not None,
            "fallback_reason": result.fallback_reason,
            "render_started_at": result.started_at,
            "render_completed_at": result.completed_at,
            "render_runtime_seconds": result.duration_seconds,
            "expected_duration_seconds": plan.expected_duration_seconds,
            "actual_duration_seconds": output_metadata.duration_seconds,
            "has_video": output_metadata.has_video,
            "has_audio": output_metadata.has_audio,
            "camera_offsets_seconds": plan.camera_offsets,
            "synchronisation": {
                "cue_type": sync_config.cue_type,
                "cue_description": sync_config.cue_description,
                "acceptance_status": sync_config.acceptance_status,
                "verification_threshold_ms": sync_config.verification_threshold_ms,
            },
            "camera_switch_count": plan.switch_count,
            "duration_metrics": {
                "common_overlap_duration": duration_metrics.common_overlap_duration,
                "total_event_coverage": duration_metrics.total_event_coverage,
                "maximum_renderable_duration": (
                    duration_metrics.maximum_renderable_duration
                ),
                "presentation_duration": duration_metrics.presentation_duration,
            },
            "command_log_path": (
                _shared_path(result.command_log_path, project_root)
                if result.command_log_path
                else None
            ),
            "warnings": all_warnings,
        },
    )
