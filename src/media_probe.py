"""FFprobe metadata extraction and rendered-output technical validation."""

from __future__ import annotations

import json
import math
import subprocess
from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path
from typing import Any

from .errors import MediaProbeError, OutputValidationError
from .models import CameraSource, DurationPolicy, MediaMetadata
from .preflight import resolve_executable


def _parse_rate(value: object) -> float:
    if not isinstance(value, str) or not value:
        return 0.0
    try:
        numerator, denominator = value.split("/", 1)
        parsed = float(numerator) / float(denominator)
    except (ValueError, ZeroDivisionError):
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return 0.0
    return parsed if math.isfinite(parsed) else 0.0


def parse_ffprobe_output(path: Path, payload: dict[str, Any]) -> MediaMetadata:
    """Convert FFprobe JSON to the subset used by the pipeline."""
    streams = payload.get("streams")
    format_data = payload.get("format")
    if not isinstance(streams, list) or not isinstance(format_data, dict):
        raise MediaProbeError(f"FFprobe returned incomplete metadata for {path}.")
    video = next(
        (
            stream
            for stream in streams
            if isinstance(stream, dict) and stream.get("codec_type") == "video"
        ),
        None,
    )
    audio = next(
        (
            stream
            for stream in streams
            if isinstance(stream, dict) and stream.get("codec_type") == "audio"
        ),
        None,
    )
    if video is None:
        raise MediaProbeError(f"Input has no video stream: {path}")
    try:
        duration = float(format_data.get("duration"))
        width = int(video.get("width"))
        height = int(video.get("height"))
    except (TypeError, ValueError) as exc:
        raise MediaProbeError(
            f"FFprobe returned invalid duration or dimensions for {path}."
        ) from exc
    fps = _parse_rate(video.get("avg_frame_rate") or video.get("r_frame_rate"))
    rotation = 0
    tags = video.get("tags")
    if isinstance(tags, dict):
        try:
            rotation = int(float(tags.get("rotate", 0)))
        except (TypeError, ValueError):
            rotation = 0
    side_data = video.get("side_data_list")
    if isinstance(side_data, list):
        for item in side_data:
            if isinstance(item, dict) and "rotation" in item:
                try:
                    rotation = int(float(item["rotation"]))
                except (TypeError, ValueError):
                    pass
                break
    if duration <= 0 or width <= 0 or height <= 0 or fps <= 0:
        raise MediaProbeError(
            f"Input metadata must have positive duration, dimensions, and frame rate: {path}"
        )
    return MediaMetadata(
        path=path,
        duration_seconds=duration,
        width=width,
        height=height,
        fps=fps,
        has_video=True,
        has_audio=audio is not None,
        video_codec=str(video.get("codec_name")) if video.get("codec_name") else None,
        audio_codec=(
            str(audio.get("codec_name"))
            if audio is not None and audio.get("codec_name")
            else None
        ),
        display_rotation=rotation,
    )


def probe_video(
    path: Path, *, ffprobe_executable: str | Path | None = None
) -> MediaMetadata:
    """Run FFprobe safely and parse its JSON response."""
    executable = (
        str(ffprobe_executable)
        if ffprobe_executable is not None
        else resolve_executable("ffprobe")
    )
    if not executable:
        raise MediaProbeError(
            "FFprobe executable was not found. Install FFmpeg and ensure ffprobe is on PATH."
        )
    command = [
        executable,
        "-v",
        "error",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        str(path),
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise MediaProbeError(f"Could not execute FFprobe for {path}: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip()[-1000:]
        raise MediaProbeError(
            f"FFprobe failed for {path} with exit code {completed.returncode}: {detail}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise MediaProbeError(f"FFprobe returned invalid JSON for {path}.") from exc
    return parse_ffprobe_output(path, payload)


def probe_cameras(
    cameras: Iterable[CameraSource], *, ffprobe_executable: str | Path | None = None
) -> tuple[CameraSource, ...]:
    probed: list[CameraSource] = []
    for camera in cameras:
        metadata = probe_video(camera.path, ffprobe_executable=ffprobe_executable)
        probed.append(
            replace(
                camera,
                duration_seconds=metadata.duration_seconds,
                width=metadata.width,
                height=metadata.height,
                fps=metadata.fps,
                has_audio=metadata.has_audio,
                video_codec=metadata.video_codec,
                audio_codec=metadata.audio_codec,
            )
        )
    return tuple(probed)


def validate_output(
    metadata: MediaMetadata,
    policy: DurationPolicy,
    *,
    expected_duration_seconds: float,
    presentation_duration_seconds: float = 0.0,
    tolerance_seconds: float = 0.75,
) -> tuple[str, ...]:
    """Validate streams and both contractual and expected duration."""
    errors: list[str] = []
    warnings: list[str] = []
    if not metadata.has_video:
        errors.append("Rendered output has no video stream.")
    if not metadata.has_audio:
        errors.append("Rendered output has no audio stream.")
    contractual_duration = metadata.duration_seconds
    if not policy.includes_title_and_credits:
        contractual_duration -= presentation_duration_seconds
    if not policy.min_seconds <= contractual_duration <= policy.max_seconds:
        errors.append(
            f"Configured duration calculation {contractual_duration:.3f}s is outside "
            f"{policy.min_seconds:.3f}–{policy.max_seconds:.3f}s."
        )
    difference = abs(metadata.duration_seconds - expected_duration_seconds)
    if difference > tolerance_seconds:
        errors.append(
            f"Rendered duration differs from the render plan by {difference:.3f}s "
            f"(allowed {tolerance_seconds:.3f}s)."
        )
    elif difference > 0.1:
        warnings.append(f"Rendered duration differs from plan by {difference:.3f}s.")
    if errors:
        raise OutputValidationError(
            "Output validation errors:\n- " + "\n- ".join(errors)
        )
    return tuple(warnings)
