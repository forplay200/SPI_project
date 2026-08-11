"""End-to-end validation, planning, atomic draft rendering, and evidence."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, replace
from pathlib import Path
from uuid import uuid4

from .edl import load_edl, validate_edl
from .edl_generator import calculate_duration_metrics
from .evidence import write_preflight_evidence, write_render_evidence
from .media_probe import MediaMetadata, probe_cameras, probe_video, validate_output
from .models import EDL, ProjectConfig, RenderPlan, RenderResult, SyncConfig
from .render_plan import build_render_plan
from .renderer import render_with_selected_backend
from .sync import apply_sync, load_sync_config
from .validate_inputs import ensure_runtime_directories, load_project_config


@dataclass(frozen=True)
class PreparedPipeline:
    project_root: Path
    config: ProjectConfig
    sync: SyncConfig
    edl: EDL
    plan: RenderPlan


def prepare_pipeline(
    config_path: Path,
    sync_path: Path,
    edl_path: Path,
    *,
    ffprobe_executable: str | Path | None = None,
    write_evidence: bool = True,
) -> PreparedPipeline:
    config = load_project_config(config_path)
    project_root = config_path.resolve().parent.parent
    probed_cameras = probe_cameras(
        config.cameras, ffprobe_executable=ffprobe_executable
    )
    sync_config = load_sync_config(sync_path)
    synced_cameras = apply_sync(
        probed_cameras,
        sync_config,
        expected_master_camera=config.master_camera,
    )
    config = replace(config, cameras=synced_cameras)
    edl = load_edl(edl_path)
    validate_edl(edl, config)
    plan = build_render_plan(config, edl)
    directories = ensure_runtime_directories(project_root)
    if write_evidence:
        duration_metrics = calculate_duration_metrics(
            config, allow_smoke=config.duration_policy.min_seconds < 60
        )
        write_preflight_evidence(
            directories["reports"] / f"{_safe_name(config.project)}_preflight.json",
            project_root=project_root,
            cameras=config.cameras,
            edl=edl,
            plan=plan,
            sync_config=sync_config,
            duration_metrics=duration_metrics,
        )
    return PreparedPipeline(project_root, config, sync_config, edl, plan)


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")
    return cleaned or "project"


def render_draft(
    prepared: PreparedPipeline,
    *,
    ffmpeg_executable: str | Path | None = None,
    ffprobe_executable: str | Path | None = None,
) -> tuple[RenderResult, MediaMetadata, Path]:
    """Render to temp, validate, atomically promote to draft, and record evidence."""
    directories = ensure_runtime_directories(prepared.project_root)
    stem = _safe_name(prepared.config.project)
    final_path = directories["draft"] / f"{stem}_draft.mp4"
    temp_path = directories["temp"] / f"{stem}-{uuid4().hex}.partial.mp4"
    command_log = directories["logs"] / f"{stem}_ffmpeg_command.json"
    try:
        result = render_with_selected_backend(
            prepared.plan,
            temp_path,
            ffmpeg_executable=ffmpeg_executable,
            command_log_path=command_log,
        )
        temp_metadata = probe_video(temp_path, ffprobe_executable=ffprobe_executable)
        output_warnings = validate_output(
            temp_metadata,
            prepared.config.duration_policy,
            expected_duration_seconds=prepared.plan.expected_duration_seconds,
            presentation_duration_seconds=(
                prepared.config.title.duration + prepared.config.credits.duration
            ),
        )
        os.replace(temp_path, final_path)
        promoted_result = replace(result, output_path=final_path)
        promoted_metadata = replace(temp_metadata, path=final_path)
        evidence_path = directories["reports"] / f"{stem}_render.json"
        write_render_evidence(
            evidence_path,
            project_root=prepared.project_root,
            result=promoted_result,
            output_metadata=promoted_metadata,
            plan=prepared.plan,
            sync_config=prepared.sync,
            duration_metrics=calculate_duration_metrics(
                prepared.config,
                allow_smoke=prepared.config.duration_policy.min_seconds < 60,
            ),
            warnings=output_warnings,
        )
        return promoted_result, promoted_metadata, evidence_path
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
