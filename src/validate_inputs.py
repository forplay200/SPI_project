"""Project configuration and local camera input validation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .errors import ConfigurationError
from .json_utils import read_json_object
from .models import (
    SUPPORTED_RENDERERS,
    SUPPORTED_VIDEO_EXTENSIONS,
    CameraSource,
    DurationPolicy,
    OutputSpec,
    ProjectConfig,
    TextSpec,
)


def _number(
    value: object, field: str, errors: list[str], *, minimum: float = 0
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        errors.append(f"{field} must be numeric.")
        return minimum
    result = float(value)
    if result <= minimum:
        errors.append(f"{field} must be greater than {minimum}.")
    return result


def _text(value: object, field: str, errors: list[str]) -> str:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be a non-empty string.")
        return ""
    return value.strip()


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _resolve_camera_path(raw_path: str, project_root: Path) -> Path:
    path = Path(raw_path)
    return (path if path.is_absolute() else project_root / path).resolve()


def parse_project_config(
    data: dict[str, Any],
    *,
    project_root: Path,
    require_camera_files: bool = True,
) -> ProjectConfig:
    """Validate a decoded project object and return an immutable configuration."""
    errors: list[str] = []
    project = _text(data.get("project"), "project", errors)
    master_camera = _text(data.get("master_camera"), "master_camera", errors)
    renderer_raw = _text(data.get("renderer", "moviepy"), "renderer", errors)
    if renderer_raw not in SUPPORTED_RENDERERS:
        errors.append(
            f"renderer must be one of {sorted(SUPPORTED_RENDERERS)}; got {renderer_raw!r}."
        )
    renderer = renderer_raw if renderer_raw in SUPPORTED_RENDERERS else "moviepy"
    fallback = data.get("allow_ffmpeg_fallback", True)
    if not isinstance(fallback, bool):
        errors.append("allow_ffmpeg_fallback must be true or false.")
        fallback = True

    output_data = data.get("output")
    if not isinstance(output_data, dict):
        errors.append("output must be an object.")
        output_data = {}
    width = int(_number(output_data.get("width", 1280), "output.width", errors))
    height = int(_number(output_data.get("height", 720), "output.height", errors))
    fps = int(_number(output_data.get("fps", 30), "output.fps", errors))
    video_codec = _text(
        output_data.get("video_codec", "libx264"), "output.video_codec", errors
    )
    audio_codec = _text(
        output_data.get("audio_codec", "aac"), "output.audio_codec", errors
    )

    def parse_text_spec(key: str) -> TextSpec:
        raw = data.get(key)
        if not isinstance(raw, dict):
            errors.append(f"{key} must be an object.")
            raw = {}
        return TextSpec(
            text=_text(raw.get("text"), f"{key}.text", errors),
            duration=_number(raw.get("duration"), f"{key}.duration", errors),
        )

    title = parse_text_spec("title")
    credits = parse_text_spec("credits")

    policy_data = data.get("duration_policy", {})
    if not isinstance(policy_data, dict):
        errors.append("duration_policy must be an object.")
        policy_data = {}
    min_seconds = _number(
        policy_data.get("min_seconds", 60.0), "duration_policy.min_seconds", errors
    )
    max_seconds = _number(
        policy_data.get("max_seconds", 180.0), "duration_policy.max_seconds", errors
    )
    includes = policy_data.get("includes_title_and_credits", True)
    if not isinstance(includes, bool):
        errors.append(
            "duration_policy.includes_title_and_credits must be true or false."
        )
        includes = True
    if max_seconds < min_seconds:
        errors.append("duration_policy.max_seconds must be at least min_seconds.")

    cameras_data = data.get("cameras")
    cameras: list[CameraSource] = []
    ids: list[str] = []
    if not isinstance(cameras_data, list):
        errors.append("cameras must be a list.")
        cameras_data = []
    if not 2 <= len(cameras_data) <= 4:
        errors.append("cameras must contain between two and four sources.")
    output_root = (project_root / "output").resolve()
    temp_root = (project_root / "temp").resolve()
    for index, raw_camera in enumerate(cameras_data):
        prefix = f"cameras[{index}]"
        if not isinstance(raw_camera, dict):
            errors.append(f"{prefix} must be an object.")
            continue
        camera_id = _text(raw_camera.get("id"), f"{prefix}.id", errors)
        raw_path = _text(raw_camera.get("path"), f"{prefix}.path", errors)
        path = _resolve_camera_path(raw_path or ".", project_root)
        ids.append(camera_id)
        if path.suffix.lower() not in SUPPORTED_VIDEO_EXTENSIONS:
            errors.append(
                f"{prefix}.path must use one of {sorted(SUPPORTED_VIDEO_EXTENSIONS)}: {raw_path}"
            )
        if _is_within(path, output_root) or _is_within(path, temp_root):
            errors.append(
                f"{prefix}.path cannot point inside output/ or temp/: {raw_path}"
            )
        if require_camera_files:
            if not path.is_file():
                errors.append(f"{prefix}.path is not a local file: {raw_path}")
            elif not os.access(path, os.R_OK):
                errors.append(f"{prefix}.path is not readable: {raw_path}")
        cameras.append(CameraSource(id=camera_id, path=path))

    duplicate_ids = sorted({camera_id for camera_id in ids if ids.count(camera_id) > 1})
    if duplicate_ids:
        errors.append(f"Camera IDs must be unique; duplicates: {duplicate_ids}.")
    if master_camera and master_camera not in ids:
        errors.append(
            f"master_camera {master_camera!r} is not present in configured camera IDs {ids}."
        )
    if errors:
        raise ConfigurationError(
            "Project configuration errors:\n- " + "\n- ".join(errors)
        )
    return ProjectConfig(
        project=project,
        master_camera=master_camera,
        renderer=renderer,  # type: ignore[arg-type]
        allow_ffmpeg_fallback=fallback,
        output=OutputSpec(
            width=width,
            height=height,
            fps=fps,
            video_codec=video_codec,
            audio_codec=audio_codec,
        ),
        title=title,
        credits=credits,
        cameras=tuple(cameras),
        duration_policy=DurationPolicy(
            min_seconds=min_seconds,
            max_seconds=max_seconds,
            includes_title_and_credits=includes,
        ),
    )


def load_project_config(
    path: Path, *, require_camera_files: bool = True
) -> ProjectConfig:
    """Load project JSON; relative camera paths are anchored at the repository root."""
    resolved = path.resolve()
    project_root = resolved.parent.parent
    return parse_project_config(
        read_json_object(resolved, label="Project configuration"),
        project_root=project_root,
        require_camera_files=require_camera_files,
    )


def ensure_runtime_directories(project_root: Path) -> dict[str, Path]:
    """Create only the pipeline-owned output directories."""
    result = {
        "draft": project_root / "output" / "draft",
        "final": project_root / "output" / "final",
        "temp": project_root / "temp",
        "logs": project_root / "evidence" / "logs",
        "reports": project_root / "evidence" / "reports",
        "approvals": project_root / "evidence" / "approvals",
    }
    for path in result.values():
        path.mkdir(parents=True, exist_ok=True)
        if not path.is_dir():
            raise ConfigurationError(
                f"Required runtime path is not a directory: {path}"
            )
    return result
