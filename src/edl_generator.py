"""Deterministic, rule-based EDL proposal generation."""

from __future__ import annotations

import math
from dataclasses import asdict
from pathlib import Path

from .edl import parse_edl_data, validate_edl
from .errors import PreparationError
from .evidence import utc_now
from .json_utils import write_generated_json, write_json_atomic
from .models import EDL, CameraSource, ProjectConfig
from .render_plan import build_render_plan


def common_usable_timeline(
    cameras: tuple[CameraSource, ...],
) -> tuple[float, float]:
    if len(cameras) < 2:
        raise PreparationError("EDL generation requires at least two cameras.")
    missing = [camera.id for camera in cameras if camera.duration_seconds is None]
    if missing:
        raise PreparationError(
            f"Camera durations must be probed before EDL generation: {missing}."
        )
    common_start = max(max(0.0, -camera.offset_seconds) for camera in cameras)
    common_end = min(
        float(camera.duration_seconds) - camera.offset_seconds
        for camera in cameras
        if camera.duration_seconds is not None
    )
    if common_end <= common_start:
        raise PreparationError(
            "The selected cameras have no common synchronized usable timeline."
        )
    return round(common_start, 6), round(common_end, 6)


def maximum_honest_output_duration(config: ProjectConfig) -> float:
    start, end = common_usable_timeline(config.cameras)
    return round(end - start + config.title.duration + config.credits.duration, 6)


def _segment_count(
    main_duration: float,
    *,
    minimum_shot_seconds: float,
    preferred_shot_seconds: float,
    maximum_shot_seconds: float,
    allow_smoke: bool,
) -> int:
    if allow_smoke:
        return 4
    count = max(4, math.ceil(main_duration / preferred_shot_seconds))
    count = max(count, math.ceil(main_duration / maximum_shot_seconds))
    maximum_count = math.floor(main_duration / minimum_shot_seconds)
    if maximum_count < 4:
        raise PreparationError(
            "The requested main timeline cannot provide four safe shots at the "
            f"{minimum_shot_seconds:.1f}s minimum."
        )
    return min(count, maximum_count)


def generate_edl(
    config: ProjectConfig,
    *,
    requested_duration_seconds: float,
    allow_smoke: bool = False,
    minimum_shot_seconds: float = 8.0,
    preferred_shot_seconds: float = 12.0,
    maximum_shot_seconds: float = 20.0,
    output_path: Path | None = None,
    report_path: Path | None = None,
    overwrite: bool = False,
) -> tuple[EDL, dict[str, object]]:
    """Generate and validate a contiguous camera-rotation EDL."""
    if not allow_smoke and not 60 <= requested_duration_seconds <= 180:
        raise PreparationError(
            "Requested duration must be between 60 and 180 seconds. Use "
            "--allow-smoke only for a clearly labelled non-acceptance render."
        )
    presentation = config.title.duration + config.credits.duration
    main_duration = requested_duration_seconds - presentation
    if main_duration <= 0:
        raise PreparationError(
            "Requested duration must exceed the configured title and credit duration."
        )
    common_start, common_end = common_usable_timeline(config.cameras)
    maximum_output = maximum_honest_output_duration(config)
    if main_duration > common_end - common_start + 0.001:
        limiting = [
            {
                "camera_id": camera.id,
                "duration_seconds": camera.duration_seconds,
                "offset_seconds": camera.offset_seconds,
            }
            for camera in config.cameras
        ]
        raise PreparationError(
            f"Requested output is {requested_duration_seconds:.3f}s but the maximum "
            f"honest synchronized output is {maximum_output:.3f}s. Limiting cameras: "
            f"{limiting}."
        )
    count = _segment_count(
        main_duration,
        minimum_shot_seconds=minimum_shot_seconds,
        preferred_shot_seconds=preferred_shot_seconds,
        maximum_shot_seconds=maximum_shot_seconds,
        allow_smoke=allow_smoke,
    )
    camera_ids = [camera.id for camera in config.cameras]
    boundaries = [
        round(common_start + (main_duration * index / count), 6)
        for index in range(count + 1)
    ]
    timeline: list[dict[str, object]] = []
    for index in range(count):
        camera_id = camera_ids[index % len(camera_ids)]
        if index == 0:
            action = "fade_in"
            reason = "Selected as the opening camera by the deterministic master-camera rule."
        elif index == count - 1:
            action = "fade_to_black"
            reason = (
                "Rule-based rotation selected the next available camera and applied "
                "the required closing transition."
            )
        elif index < 4:
            action = "cut"
            reason = "Selected to satisfy the minimum multi-camera switch requirement."
        else:
            action = "cut"
            reason = (
                "Rule-based rotation selected the next available camera after the "
                "preferred shot duration."
            )
        item: dict[str, object] = {
            "id": f"generated-{index + 1:03d}",
            "start": boundaries[index],
            "end": boundaries[index + 1],
            "camera": camera_id,
            "reason": reason,
            "action": action,
        }
        if index == 1:
            shot_duration = boundaries[index + 1] - boundaries[index]
            overlay_start = boundaries[index] + min(1.0, shot_duration * 0.2)
            overlay_end = min(
                boundaries[index + 1],
                overlay_start + min(4.0, shot_duration * 0.5),
            )
            item["overlay"] = {
                "type": "lower_third",
                "text": "Kindergarten Graduation Ceremony",
                "start": round(overlay_start, 6),
                "end": round(overlay_end, 6),
                "position": "bottom",
            }
        timeline.append(item)
    data: dict[str, object] = {
        "project": config.project,
        "timeline": timeline,
    }
    edl = parse_edl_data(data)
    validate_edl(edl, config)
    plan = build_render_plan(config, edl)
    metadata: dict[str, object] = {
        "generated_at": utc_now(),
        "generated_by": "deterministic_rule_based_edl_generator",
        "generation_rule": "contiguous_round_robin_camera_rotation",
        "requires_human_review": True,
        "machine_learning_used": False,
        "requested_duration_seconds": requested_duration_seconds,
        "maximum_honest_duration_seconds": maximum_output,
        "common_timeline": {"start": common_start, "end": common_end},
        "shot_policy": {
            "minimum_seconds": minimum_shot_seconds,
            "preferred_seconds": preferred_shot_seconds,
            "maximum_seconds": maximum_shot_seconds,
        },
        "smoke": allow_smoke,
        "segment_count": len(edl.timeline),
        "switch_count": edl.switch_count,
        "expected_output_duration_seconds": plan.expected_duration_seconds,
        "decisions": [asdict(segment) for segment in edl.timeline],
    }
    if output_path is not None:
        write_generated_json(output_path, data, overwrite=overwrite)
    if report_path is not None:
        write_json_atomic(report_path, metadata)
    return edl, metadata
