"""JSON EDL parsing and semantic validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import EDLParseError, EDLValidationError
from .models import (
    EDL,
    SUPPORTED_ACTIONS,
    SUPPORTED_OVERLAY_TYPES,
    EDLSegment,
    OverlaySpec,
    ProjectConfig,
)


def _is_number(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float))


def _parse_overlay(
    value: object,
    segment_id: str,
    segment_start: float,
    segment_end: float,
    errors: list[str],
) -> OverlaySpec | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        errors.append(f"Segment {segment_id!r} overlay must be an object.")
        return None
    overlay_type = value.get("type")
    text = value.get("text")
    start = value.get("start")
    end = value.get("end")
    position = value.get("position", "bottom")
    if overlay_type not in SUPPORTED_OVERLAY_TYPES:
        errors.append(
            f"Segment {segment_id!r} overlay.type must be one of "
            f"{sorted(SUPPORTED_OVERLAY_TYPES)}."
        )
        overlay_type = "label"
    if not isinstance(text, str) or not text.strip():
        errors.append(f"Segment {segment_id!r} overlay.text must be non-empty.")
        text = ""
    if start is not None and not _is_number(start):
        errors.append(f"Segment {segment_id!r} overlay.start must be numeric.")
        start = None
    if end is not None and not _is_number(end):
        errors.append(f"Segment {segment_id!r} overlay.end must be numeric.")
        end = None
    start_value = float(start) if _is_number(start) else None
    end_value = float(end) if _is_number(end) else None
    effective_start = segment_start if start_value is None else start_value
    effective_end = segment_end if end_value is None else end_value
    if effective_start < segment_start or effective_end > segment_end:
        errors.append(
            f"Segment {segment_id!r} overlay times must stay within its master interval "
            f"{segment_start:.3f}–{segment_end:.3f}s."
        )
    if effective_end <= effective_start:
        errors.append(f"Segment {segment_id!r} overlay end must be greater than start.")
    if position not in {"top", "center", "bottom"}:
        errors.append(
            f"Segment {segment_id!r} overlay.position must be top, center, or bottom."
        )
        position = "bottom"
    return OverlaySpec(
        type=overlay_type,  # type: ignore[arg-type]
        text=text.strip(),
        start=start_value,
        end=end_value,
        position=position,
    )


def parse_edl_data(data: dict[str, Any]) -> EDL:
    errors: list[str] = []
    project = data.get("project")
    if not isinstance(project, str) or not project.strip():
        errors.append("project must be a non-empty string.")
        project = ""
    timeline_data = data.get("timeline")
    if not isinstance(timeline_data, list) or not timeline_data:
        raise EDLValidationError(
            "EDL validation errors:\n- timeline must be a non-empty list."
        )
    timeline: list[EDLSegment] = []
    for index, raw in enumerate(timeline_data):
        prefix = f"timeline[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{prefix} must be an object.")
            continue
        segment_id = raw.get("id")
        if not isinstance(segment_id, str) or not segment_id.strip():
            errors.append(f"{prefix}.id must be a non-empty string.")
            segment_id = f"invalid-{index}"
        start_raw = raw.get("start")
        end_raw = raw.get("end")
        if not _is_number(start_raw):
            errors.append(f"Segment {segment_id!r} start must be numeric.")
            start_raw = 0.0
        if not _is_number(end_raw):
            errors.append(f"Segment {segment_id!r} end must be numeric.")
            end_raw = 0.0
        start, end = float(start_raw), float(end_raw)
        camera = raw.get("camera")
        reason = raw.get("reason")
        action = raw.get("action")
        if not isinstance(camera, str) or not camera.strip():
            errors.append(f"Segment {segment_id!r} camera must be non-empty.")
            camera = ""
        if not isinstance(reason, str) or not reason.strip():
            errors.append(f"Segment {segment_id!r} reason must be non-empty.")
            reason = ""
        if action not in SUPPORTED_ACTIONS:
            errors.append(
                f"Segment {segment_id!r} action must be one of {sorted(SUPPORTED_ACTIONS)}."
            )
            action = "cut"
        if start < 0:
            errors.append(f"Segment {segment_id!r} start cannot be negative.")
        if end <= start:
            errors.append(f"Segment {segment_id!r} end must be greater than start.")
        overlay = _parse_overlay(raw.get("overlay"), segment_id, start, end, errors)
        timeline.append(
            EDLSegment(
                id=segment_id.strip(),
                start=start,
                end=end,
                camera=camera.strip(),
                reason=reason.strip(),
                action=action,  # type: ignore[arg-type]
                overlay=overlay,
            )
        )
    if errors:
        raise EDLValidationError("EDL validation errors:\n- " + "\n- ".join(errors))
    return EDL(project=project.strip(), timeline=tuple(timeline))


def load_edl(path: Path) -> EDL:
    try:
        with path.resolve().open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except FileNotFoundError as exc:
        raise EDLParseError(f"EDL file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EDLParseError(
            f"EDL is not valid JSON at line {exc.lineno}, column {exc.colno}: {path}"
        ) from exc
    except OSError as exc:
        raise EDLParseError(f"Cannot read EDL file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EDLParseError(f"EDL root must be a JSON object: {path}")
    return parse_edl_data(value)


def validate_edl(edl: EDL, config: ProjectConfig) -> None:
    """Enforce ordering, continuity, explainability, and assignment minimums."""
    errors: list[str] = []
    if edl.project != config.project:
        errors.append(
            f"EDL project {edl.project!r} does not match configuration project "
            f"{config.project!r}."
        )
    ids = [segment.id for segment in edl.timeline]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        errors.append(f"Segment IDs must be unique; duplicates: {duplicates}.")
    camera_ids = {camera.id for camera in config.cameras}
    for segment in edl.timeline:
        if segment.camera not in camera_ids:
            errors.append(
                f"Segment {segment.id!r} references unknown camera {segment.camera!r}; "
                f"configured cameras are {sorted(camera_ids)}."
            )
    for previous, current in zip(edl.timeline, edl.timeline[1:]):
        if current.start < previous.start:
            errors.append(
                f"Segment {current.id!r} is out of start-time order after {previous.id!r}."
            )
        if current.start < previous.end:
            errors.append(f"Segments {previous.id!r} and {current.id!r} overlap.")
        elif abs(current.start - previous.end) > 0.001:
            errors.append(
                f"Gap between segments {previous.id!r} and {current.id!r}; "
                "gaps are unsupported in the minimum prototype."
            )
    cameras_used = {segment.camera for segment in edl.timeline}
    if len(cameras_used) < 2:
        errors.append("EDL must use at least two distinct cameras.")
    if edl.switch_count < 3:
        errors.append(
            f"EDL must contain at least three camera switches; found {edl.switch_count}."
        )
    if not any(segment.action != "cut" for segment in edl.timeline):
        errors.append("EDL must contain at least one supported transition action.")
    if not any(segment.overlay is not None for segment in edl.timeline):
        errors.append(
            "EDL must contain at least one subtitle, label, or lower-third overlay."
        )
    duration = edl.main_duration_seconds
    if config.duration_policy.includes_title_and_credits:
        duration += config.title.duration + config.credits.duration
    if (
        not config.duration_policy.min_seconds
        <= duration
        <= config.duration_policy.max_seconds
    ):
        errors.append(
            f"Configured duration calculation is {duration:.3f}s, outside "
            f"{config.duration_policy.min_seconds:.3f}–"
            f"{config.duration_policy.max_seconds:.3f}s."
        )
    if errors:
        raise EDLValidationError("EDL semantic errors:\n- " + "\n- ".join(errors))
