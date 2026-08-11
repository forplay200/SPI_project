"""Deterministic, coverage-aware rule-based EDL proposal generation."""

from __future__ import annotations

import math
from dataclasses import asdict
from itertools import pairwise
from pathlib import Path

from .edl import parse_edl_data, validate_edl
from .errors import PreparationError
from .evidence import utc_now
from .json_utils import write_generated_json, write_json_atomic
from .models import (
    EDL,
    CameraSource,
    CoverageInterval,
    DurationMetrics,
    ProjectConfig,
)
from .render_plan import build_render_plan

_EPSILON = 0.001


def _coverage_intervals(
    cameras: tuple[CameraSource, ...], *, renderable_only: bool
) -> tuple[CoverageInterval, ...]:
    if len(cameras) < 2:
        raise PreparationError("EDL generation requires at least two cameras.")
    missing = [camera.id for camera in cameras if camera.duration_seconds is None]
    if missing:
        raise PreparationError(
            f"Camera durations must be probed before EDL generation: {missing}."
        )
    intervals: list[CoverageInterval] = []
    for camera in cameras:
        source_duration = float(camera.duration_seconds or 0.0)
        start = -camera.offset_seconds
        end = source_duration - camera.offset_seconds
        if renderable_only:
            # The current EDL contract uses a non-negative master timeline. Earlier
            # camera-only coverage remains visible in total_event_coverage, but is
            # not silently rebased because that would change synchronization data.
            start = max(0.0, start)
        if end > start + _EPSILON:
            intervals.append(
                CoverageInterval(camera.id, round(start, 6), round(end, 6))
            )
    return tuple(intervals)


def _merged_intervals(
    intervals: tuple[CoverageInterval, ...],
) -> tuple[tuple[float, float], ...]:
    ordered = sorted(
        ((item.start_seconds, item.end_seconds) for item in intervals),
        key=lambda item: (item[0], item[1]),
    )
    merged: list[list[float]] = []
    for start, end in ordered:
        if not merged or start > merged[-1][1] + _EPSILON:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return tuple((round(start, 6), round(end, 6)) for start, end in merged)


def common_usable_timeline(
    cameras: tuple[CameraSource, ...],
) -> tuple[float, float]:
    """Return all-camera overlap for synchronization diagnostics only."""
    intervals = _coverage_intervals(cameras, renderable_only=True)
    by_camera = {item.camera_id: item for item in intervals}
    if len(by_camera) != len(cameras):
        return 0.0, 0.0
    common_start = max(item.start_seconds for item in by_camera.values())
    common_end = min(item.end_seconds for item in by_camera.values())
    if common_end <= common_start:
        return round(common_start, 6), round(common_start, 6)
    return round(common_start, 6), round(common_end, 6)


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
    maximum_count = math.floor((main_duration + _EPSILON) / minimum_shot_seconds)
    if maximum_count < 4:
        raise PreparationError(
            "The requested main timeline cannot provide four safe shots at the "
            f"{minimum_shot_seconds:.1f}s minimum."
        )
    return min(count, maximum_count)


def _candidate_window_starts(
    *,
    component: tuple[float, float],
    intervals: tuple[CoverageInterval, ...],
    main_duration: float,
    segment_count: int,
) -> tuple[float, ...]:
    component_start, component_end = component
    latest_start = component_end - main_duration
    if latest_start < component_start - _EPSILON:
        return ()
    shot_duration = main_duration / segment_count
    candidates = {component_start, latest_start}
    boundaries = {
        value
        for item in intervals
        for value in (item.start_seconds, item.end_seconds)
        if component_start - _EPSILON <= value <= component_end + _EPSILON
    }
    for boundary in boundaries:
        for index in range(segment_count + 1):
            candidates.add(boundary - index * shot_duration)
    return tuple(
        sorted(
            round(max(component_start, min(latest_start, value)), 6)
            for value in candidates
            if component_start - _EPSILON <= value <= latest_start + _EPSILON
        )
    )


def _camera_sequence(
    candidates_by_segment: list[tuple[str, ...]], *, master_camera: str
) -> tuple[str, ...] | None:
    states: dict[tuple[str, frozenset[str], int], tuple[str, ...]] = {}
    for camera_id in candidates_by_segment[0]:
        states[(camera_id, frozenset((camera_id,)), 0)] = (camera_id,)
    for candidates in candidates_by_segment[1:]:
        next_states: dict[tuple[str, frozenset[str], int], tuple[str, ...]] = {}
        for (last, used, switches), sequence in states.items():
            for camera_id in candidates:
                next_switches = switches + int(camera_id != last)
                key = (camera_id, used | {camera_id}, next_switches)
                proposed = sequence + (camera_id,)
                existing = next_states.get(key)
                if existing is None or proposed < existing:
                    next_states[key] = proposed
        states = next_states
        if not states:
            return None
    valid = [
        (switches, used, sequence)
        for (_, used, switches), sequence in states.items()
        if switches >= 3 and len(used) >= 2
    ]
    if not valid:
        return None
    valid.sort(
        key=lambda item: (
            item[2][0] != master_camera,
            -item[0],
            -len(item[1]),
            item[2],
        )
    )
    return valid[0][2]


def _find_schedule(
    config: ProjectConfig,
    *,
    main_duration: float,
    minimum_shot_seconds: float,
    preferred_shot_seconds: float,
    maximum_shot_seconds: float,
    allow_smoke: bool,
) -> tuple[tuple[float, ...], tuple[str, ...]] | None:
    try:
        count = _segment_count(
            main_duration,
            minimum_shot_seconds=minimum_shot_seconds,
            preferred_shot_seconds=preferred_shot_seconds,
            maximum_shot_seconds=maximum_shot_seconds,
            allow_smoke=allow_smoke,
        )
    except PreparationError:
        return None
    intervals = _coverage_intervals(config.cameras, renderable_only=True)
    components = _merged_intervals(intervals)
    for component in sorted(
        components, key=lambda item: (-(item[1] - item[0]), item[0])
    ):
        for start in _candidate_window_starts(
            component=component,
            intervals=intervals,
            main_duration=main_duration,
            segment_count=count,
        ):
            boundaries = tuple(
                round(start + main_duration * index / count, 6)
                for index in range(count + 1)
            )
            candidates_by_segment: list[tuple[str, ...]] = []
            for segment_start, segment_end in pairwise(boundaries):
                available = tuple(
                    sorted(
                        item.camera_id
                        for item in intervals
                        if item.start_seconds <= segment_start + _EPSILON
                        and item.end_seconds >= segment_end - _EPSILON
                    )
                )
                if not available:
                    break
                candidates_by_segment.append(available)
            if len(candidates_by_segment) != count:
                continue
            sequence = _camera_sequence(
                candidates_by_segment, master_camera=config.master_camera
            )
            if sequence is not None:
                return boundaries, sequence
    return None


def _maximum_renderable_main_duration(
    config: ProjectConfig,
    *,
    minimum_shot_seconds: float,
    preferred_shot_seconds: float,
    maximum_shot_seconds: float,
    allow_smoke: bool,
) -> float:
    presentation = config.title.duration + config.credits.duration
    policy_cap = max(0.0, config.duration_policy.max_seconds - presentation)
    components = _merged_intervals(
        _coverage_intervals(config.cameras, renderable_only=True)
    )
    upper = min(
        policy_cap,
        max((end - start for start, end in components), default=0.0),
    )
    minimum = 0.01 if allow_smoke else minimum_shot_seconds * 4
    if upper < minimum - _EPSILON:
        return 0.0
    candidate = upper
    last_failed = upper
    while candidate >= minimum - _EPSILON:
        schedule = _find_schedule(
            config,
            main_duration=candidate,
            minimum_shot_seconds=minimum_shot_seconds,
            preferred_shot_seconds=preferred_shot_seconds,
            maximum_shot_seconds=maximum_shot_seconds,
            allow_smoke=allow_smoke,
        )
        if schedule is not None:
            low = candidate
            high = last_failed
            for _ in range(12):
                probe = (low + high) / 2
                if (
                    _find_schedule(
                        config,
                        main_duration=probe,
                        minimum_shot_seconds=minimum_shot_seconds,
                        preferred_shot_seconds=preferred_shot_seconds,
                        maximum_shot_seconds=maximum_shot_seconds,
                        allow_smoke=allow_smoke,
                    )
                    is not None
                ):
                    low = probe
                else:
                    high = probe
            return round(low, 6)
        last_failed = candidate
        candidate -= 0.25
    return 0.0


def calculate_duration_metrics(
    config: ProjectConfig,
    *,
    minimum_shot_seconds: float = 8.0,
    preferred_shot_seconds: float = 12.0,
    maximum_shot_seconds: float = 20.0,
    allow_smoke: bool = False,
) -> DurationMetrics:
    """Calculate separate sync overlap, event union, and EDL renderability."""
    raw_intervals = _coverage_intervals(config.cameras, renderable_only=False)
    common_start, common_end = common_usable_timeline(config.cameras)
    common_overlap = max(0.0, common_end - common_start)
    event_coverage = sum(end - start for start, end in _merged_intervals(raw_intervals))
    presentation = config.title.duration + config.credits.duration
    maximum_main = _maximum_renderable_main_duration(
        config,
        minimum_shot_seconds=minimum_shot_seconds,
        preferred_shot_seconds=preferred_shot_seconds,
        maximum_shot_seconds=maximum_shot_seconds,
        allow_smoke=allow_smoke,
    )
    maximum_output = maximum_main + presentation if maximum_main > 0 else 0.0
    return DurationMetrics(
        common_overlap_duration=round(common_overlap, 6),
        total_event_coverage=round(event_coverage, 6),
        maximum_renderable_duration=round(maximum_output, 6),
        presentation_duration=round(presentation, 6),
        coverage_intervals=raw_intervals,
    )


def maximum_honest_output_duration(config: ProjectConfig) -> float:
    """Compatibility wrapper for the corrected renderability calculation."""
    return calculate_duration_metrics(config).maximum_renderable_duration


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
    """Generate a contiguous EDL from per-segment synchronized coverage."""
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
    metrics = calculate_duration_metrics(
        config,
        minimum_shot_seconds=minimum_shot_seconds,
        preferred_shot_seconds=preferred_shot_seconds,
        maximum_shot_seconds=maximum_shot_seconds,
        allow_smoke=allow_smoke,
    )
    if requested_duration_seconds > metrics.maximum_renderable_duration + _EPSILON:
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
            "renderable output from coverage-aware camera assignment is "
            f"{metrics.maximum_renderable_duration:.3f}s. Limiting cameras: "
            f"{limiting}."
        )
    schedule = _find_schedule(
        config,
        main_duration=main_duration,
        minimum_shot_seconds=minimum_shot_seconds,
        preferred_shot_seconds=preferred_shot_seconds,
        maximum_shot_seconds=maximum_shot_seconds,
        allow_smoke=allow_smoke,
    )
    if schedule is None:
        raise PreparationError(
            "No valid coverage-aware camera sequence can satisfy the requested "
            "duration, minimum shot duration, and three-switch rule."
        )
    boundaries, camera_sequence = schedule
    timeline: list[dict[str, object]] = []
    for index, camera_id in enumerate(camera_sequence):
        if index == 0:
            action = "fade_in"
            reason = (
                "Selected as the opening camera by the deterministic master-camera rule."
                if camera_id == config.master_camera
                else "Selected because the master camera does not cover the complete opening interval."
            )
        elif index == len(camera_sequence) - 1:
            action = "fade_to_black"
            reason = (
                "Selected from the cameras covering the closing interval and applied "
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
    data: dict[str, object] = {"project": config.project, "timeline": timeline}
    edl = parse_edl_data(data)
    validate_edl(edl, config)
    plan = build_render_plan(config, edl)
    metadata: dict[str, object] = {
        "generated_at": utc_now(),
        "generated_by": "deterministic_rule_based_edl_generator",
        "generation_rule": "coverage_aware_camera_rotation",
        "requires_human_review": True,
        "machine_learning_used": False,
        "requested_duration_seconds": requested_duration_seconds,
        "common_overlap_duration": metrics.common_overlap_duration,
        "total_event_coverage": metrics.total_event_coverage,
        "maximum_renderable_duration": metrics.maximum_renderable_duration,
        "presentation_duration": metrics.presentation_duration,
        "coverage_intervals": [asdict(item) for item in metrics.coverage_intervals],
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
