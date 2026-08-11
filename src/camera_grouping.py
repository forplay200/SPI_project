"""Evidence-based deterministic grouping of local multi-camera recordings."""

from __future__ import annotations

import itertools
import re
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .errors import PreparationError
from .evidence import utc_now
from .json_utils import write_json_atomic
from .models import (
    CameraGroupingResult,
    CameraGroupingState,
    DiscoveredVideo,
    PairwiseCameraScore,
)
from .sync_assistant import (
    FRAME_SECONDS,
    decode_audio_window,
    detect_transient_candidates,
    estimate_envelope_offset,
    rank_alignment_offsets,
)

PAIR_ACCEPTANCE_SCORE = 0.56
HIGH_CONFIDENCE_SCORE = 0.75
GROUP_EXPANSION_SCORE_MARGIN = 0.05
MINIMUM_AUDIO_CORRELATION = 0.45
SCORING_WEIGHTS = {
    "audio_correlation": 0.42,
    "offset_stability": 0.13,
    "shared_transients": 0.10,
    "filename_time": 0.06,
    "creation_time": 0.04,
    "duration_compatibility": 0.08,
    "common_duration": 0.08,
    "audio_availability": 0.04,
    "source_confidence": 0.05,
    "derived_duplicate_penalty": -0.80,
}


def normalise_filename_timestamp(path: Path | str) -> datetime | None:
    """Parse common compact/separated date-time camera filenames."""
    stem = Path(path).stem
    match = re.search(
        r"(?<!\d)(?P<date>20\d{6})[^0-9]*(?P<time>[0-2]\d[0-5]\d[0-5]\d)(?!\d)",
        stem,
    )
    if not match:
        return None
    try:
        return datetime.strptime(
            match.group("date") + match.group("time"), "%Y%m%d%H%M%S"
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _metadata_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        return (
            parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
        )
    except ValueError:
        return None


def _time_distance(first: datetime | None, second: datetime | None) -> float | None:
    if first is None or second is None:
        return None
    return abs(first.timestamp() - second.timestamp())


def _time_signal(distance_seconds: float | None) -> float:
    if distance_seconds is None:
        return 0.0
    if distance_seconds <= 120:
        return 1.0
    if distance_seconds <= 15 * 60:
        return 0.7
    if distance_seconds <= 12 * 60 * 60:
        return 0.3
    return 0.0


def _common_duration(
    first_duration: float, second_duration: float, offset: float
) -> float:
    start = max(0.0, -offset)
    end = min(first_duration, second_duration - offset)
    return max(0.0, end - start)


def _analysis_windows(
    first: np.ndarray, second: np.ndarray
) -> tuple[tuple[np.ndarray, np.ndarray], ...]:
    minimum = min(len(first), len(second))
    five_seconds = max(1, round(5.0 / FRAME_SECONDS))
    window_size = min(minimum, five_seconds)
    if window_size <= 2:
        return ()
    positions = [0]
    if minimum >= window_size * 2:
        positions.append((minimum - window_size) // 2)
    if minimum >= window_size * 3:
        positions.append(minimum - window_size)
    return tuple(
        (
            first[start : start + window_size],
            second[start : start + window_size],
        )
        for start in dict.fromkeys(positions)
    )


def _window_evidence(
    first: np.ndarray, second: np.ndarray
) -> tuple[tuple[float, ...], tuple[float, ...], float]:
    offsets: list[float] = []
    correlations: list[float] = []
    for first_window, second_window in _analysis_windows(first, second):
        offset, correlation = estimate_envelope_offset(
            first_window, second_window, maximum_offset_seconds=3.0
        )
        offsets.append(offset)
        correlations.append(max(0.0, correlation))
    supported_offsets = [
        offset
        for offset, correlation in zip(offsets, correlations)
        if correlation >= 0.35
    ]
    if len(supported_offsets) >= 2:
        spread = float(np.std(supported_offsets))
        stability = max(0.0, min(1.0, 1.0 - (spread / 0.35)))
    elif supported_offsets:
        stability = 0.45
    else:
        stability = 0.0
    return tuple(offsets), tuple(correlations), stability


def _shared_transient_evidence(
    first_samples: np.ndarray,
    second_samples: np.ndarray,
    offset_seconds: float,
) -> tuple[int, float]:
    first = detect_transient_candidates(first_samples)
    second = detect_transient_candidates(second_samples)
    matches: list[float] = []
    used: set[int] = set()
    for first_item in first:
        best: tuple[float, int, float] | None = None
        for index, second_item in enumerate(second):
            if index in used:
                continue
            difference = abs(
                (second_item.timestamp_seconds - first_item.timestamp_seconds)
                - offset_seconds
            )
            if difference <= 0.16:
                strength = min(first_item.confidence, second_item.confidence)
                candidate = (difference, index, strength)
                if best is None or candidate < best:
                    best = candidate
        if best is not None:
            used.add(best[1])
            matches.append(best[2])
    return len(matches), (sum(matches) / len(matches) if matches else 0.0)


def _derived_duplicate_likelihood(
    first: DiscoveredVideo,
    second: DiscoveredVideo,
    audio_correlation: float,
    offset_seconds: float | None,
) -> float:
    if first.duration_seconds is None or second.duration_seconds is None:
        return 0.0
    same_stream_shape = (
        first.width == second.width
        and first.height == second.height
        and first.video_codec == second.video_codec
        and first.fps is not None
        and second.fps is not None
        and abs(first.fps - second.fps) <= 0.01
    )
    duration_difference = abs(first.duration_seconds - second.duration_seconds)
    near_zero_offset = offset_seconds is not None and abs(offset_seconds) <= 0.02
    if (
        audio_correlation >= 0.995
        and duration_difference <= 0.05
        and same_stream_shape
        and near_zero_offset
    ):
        return 1.0
    if (
        audio_correlation >= 0.985
        and duration_difference <= 0.1
        and same_stream_shape
        and near_zero_offset
    ):
        return 0.7
    return 0.0


def score_camera_pair(
    first: DiscoveredVideo,
    second: DiscoveredVideo,
    *,
    first_samples: np.ndarray | None,
    second_samples: np.ndarray | None,
    minimum_common_duration_seconds: float,
) -> PairwiseCameraScore:
    duration_a = first.duration_seconds or 0.0
    duration_b = second.duration_seconds or 0.0
    duration_compatibility = (
        min(duration_a, duration_b) / max(duration_a, duration_b)
        if duration_a > 0 and duration_b > 0
        else 0.0
    )
    audio_available = (
        first_samples is not None
        and second_samples is not None
        and bool(len(first_samples))
        and bool(len(second_samples))
    )
    offset: float | None = None
    correlation = 0.0
    window_offsets: tuple[float, ...] = ()
    window_correlations: tuple[float, ...] = ()
    stability = 0.0
    shared_count = 0
    shared_strength = 0.0
    if audio_available:
        alternatives = rank_alignment_offsets(
            first_samples,
            second_samples,
            maximum_offset_seconds=min(
                60.0,
                max(duration_a, duration_b, 5.0),
            ),
        )
        if alternatives:
            best = alternatives[0]
            offset = float(best["offset_seconds"])
            correlation = max(0.0, float(best["audio_correlation"]))
            stability = float(best["offset_stability"])
            window_offsets = tuple(
                float(value) for value in best["window_offsets_seconds"]
            )
            window_correlations = tuple(
                float(value) for value in best["window_correlations"]
            )
            shared_count, shared_strength = _shared_transient_evidence(
                first_samples, second_samples, offset
            )
    common_duration = _common_duration(duration_a, duration_b, offset or 0.0)
    filename_distance = _time_distance(
        normalise_filename_timestamp(first.path),
        normalise_filename_timestamp(second.path),
    )
    creation_distance = _time_distance(
        _metadata_timestamp(first.creation_time),
        _metadata_timestamp(second.creation_time),
    )
    transient_signal = min(1.0, (shared_count / 3.0) * 0.6 + shared_strength * 0.4)
    common_signal = min(
        1.0,
        common_duration / max(1.0, minimum_common_duration_seconds),
    )
    source_confidence = (
        float(first.classification == "likely_source")
        + float(second.classification == "likely_source")
    ) / 2.0
    duplicate_likelihood = _derived_duplicate_likelihood(
        first, second, correlation, offset
    )
    score = (
        correlation * SCORING_WEIGHTS["audio_correlation"]
        + stability * SCORING_WEIGHTS["offset_stability"]
        + transient_signal * SCORING_WEIGHTS["shared_transients"]
        + _time_signal(filename_distance) * SCORING_WEIGHTS["filename_time"]
        + _time_signal(creation_distance) * SCORING_WEIGHTS["creation_time"]
        + duration_compatibility * SCORING_WEIGHTS["duration_compatibility"]
        + common_signal * SCORING_WEIGHTS["common_duration"]
        + float(audio_available) * SCORING_WEIGHTS["audio_availability"]
        + source_confidence * SCORING_WEIGHTS["source_confidence"]
        + duplicate_likelihood * SCORING_WEIGHTS["derived_duplicate_penalty"]
    )
    score = max(0.0, min(1.0, score))
    accepted = (
        audio_available
        and correlation >= MINIMUM_AUDIO_CORRELATION
        and common_duration >= minimum_common_duration_seconds
        and duplicate_likelihood < 0.7
        and score >= PAIR_ACCEPTANCE_SCORE
    )
    confidence = (
        "high"
        if accepted and score >= HIGH_CONFIDENCE_SCORE and stability >= 0.6
        else ("medium" if accepted else "low")
    )
    if duplicate_likelihood >= 0.7:
        reason = "Rejected as a likely derived duplicate, not an independent camera."
    elif not audio_available:
        reason = "Rejected because both files need usable audio for automatic grouping."
    elif common_duration < minimum_common_duration_seconds:
        reason = "Rejected because the estimated common usable duration is too short."
    elif correlation < MINIMUM_AUDIO_CORRELATION:
        reason = "Rejected because cross-camera audio correlation is too weak."
    elif score < PAIR_ACCEPTANCE_SCORE:
        reason = "Rejected because the weighted evidence score is below threshold."
    else:
        reason = (
            "Accepted from local audio correlation, offset stability, transient, "
            "timing, duration, and source evidence; synchronization remains unverified."
        )
    return PairwiseCameraScore(
        camera_a=first.camera_id or "unassigned",
        camera_b=second.camera_id or "unassigned",
        path_a=first.relative_path,
        path_b=second.relative_path,
        filename_time_distance_seconds=filename_distance,
        creation_time_distance_seconds=creation_distance,
        duration_compatibility=round(duration_compatibility, 6),
        common_usable_duration_seconds=round(common_duration, 6),
        audio_available=audio_available,
        audio_correlation=round(correlation, 6),
        estimated_offset_seconds=round(offset, 6) if offset is not None else None,
        offset_stability=round(stability, 6),
        shared_transient_count=shared_count,
        shared_transient_strength=round(shared_strength, 6),
        source_confidence=round(source_confidence, 6),
        derived_duplicate_likelihood=round(duplicate_likelihood, 6),
        total_score=round(score, 6),
        confidence=confidence,
        accepted=accepted,
        reason=reason,
        window_offsets_seconds=tuple(round(value, 6) for value in window_offsets),
        window_correlations=tuple(round(value, 6) for value in window_correlations),
    )


def _resolve_explicit_selection(
    eligible: tuple[DiscoveredVideo, ...],
    requested: tuple[Path, ...],
    input_path: Path,
) -> tuple[DiscoveredVideo, ...]:
    if not 2 <= len(requested) <= 4:
        raise PreparationError(
            "Explicit selection requires two to four --camera-file values."
        )
    selected: list[DiscoveredVideo] = []
    for raw in requested:
        candidate = (raw if raw.is_absolute() else input_path / raw).resolve()
        matches = [video for video in eligible if video.path.resolve() == candidate]
        if not matches and len(raw.parts) == 1:
            matches = [video for video in eligible if video.path.name == raw.name]
        if len(matches) != 1:
            raise PreparationError(
                f"Explicit camera file must identify one eligible source: {raw}"
            )
        if matches[0] in selected:
            raise PreparationError(f"Explicit camera file was repeated: {raw}")
        selected.append(matches[0])
    return tuple(sorted(selected, key=lambda video: video.camera_id or ""))


def group_camera_sources(
    videos: tuple[DiscoveredVideo, ...],
    *,
    input_path: Path,
    ffmpeg_executable: str | Path | None = None,
    analysis_seconds: float = 120.0,
    minimum_common_duration_seconds: float = 8.0,
    explicit_camera_files: tuple[Path, ...] = (),
    report_path: Path | None = None,
) -> CameraGroupingResult:
    """Analyse every eligible pair once and select a deterministic compatible group."""
    eligible = tuple(
        sorted(
            (video for video in videos if video.usable),
            key=lambda video: video.camera_id or "",
        )
    )
    excluded_derived = sum(
        video.classification == "likely_derived_output" for video in videos
    )
    if explicit_camera_files:
        selected = _resolve_explicit_selection(
            eligible, explicit_camera_files, input_path.resolve()
        )
        result = CameraGroupingResult(
            state=CameraGroupingState.CAMERA_GROUP_CONFIRMED,
            selected_videos=selected,
            pair_scores=(),
            eligible_count=len(eligible),
            excluded_derived_count=excluded_derived,
            analysed_pair_count=0,
            best_score=None,
            confidence="explicit",
            reason="Explicit local camera selection bypassed only automatic grouping.",
            suggested_videos=(),
            report_path=report_path,
        )
        _write_grouping_report(result, report_path)
        return result
    if len(eligible) < 2:
        state = (
            CameraGroupingState.DERIVED_OUTPUTS_ONLY
            if excluded_derived and not eligible
            else CameraGroupingState.NO_RELIABLE_CAMERA_GROUP
        )
        result = CameraGroupingResult(
            state=state,
            selected_videos=(),
            pair_scores=(),
            eligible_count=len(eligible),
            excluded_derived_count=excluded_derived,
            analysed_pair_count=0,
            best_score=None,
            confidence="none",
            reason="Fewer than two eligible source videos remain after discovery.",
            suggested_videos=(),
            report_path=report_path,
        )
        _write_grouping_report(result, report_path)
        return result

    sample_cache: dict[str, np.ndarray | None] = {}
    for video in eligible:
        if not video.has_audio:
            sample_cache[video.camera_id or video.relative_path] = None
            continue
        duration = min(analysis_seconds, video.duration_seconds or analysis_seconds)
        try:
            sample_cache[video.camera_id or video.relative_path] = decode_audio_window(
                video.path,
                search_window_seconds=duration,
                ffmpeg_executable=ffmpeg_executable,
            )
        except PreparationError:
            sample_cache[video.camera_id or video.relative_path] = None

    pairs = tuple(
        score_camera_pair(
            first,
            second,
            first_samples=sample_cache[first.camera_id or first.relative_path],
            second_samples=sample_cache[second.camera_id or second.relative_path],
            minimum_common_duration_seconds=minimum_common_duration_seconds,
        )
        for first, second in itertools.combinations(eligible, 2)
    )
    pair_map = {frozenset((pair.camera_a, pair.camera_b)): pair for pair in pairs}
    compatible_groups: list[tuple[tuple[DiscoveredVideo, ...], float, float]] = []
    for size in range(2, min(4, len(eligible)) + 1):
        for combination in itertools.combinations(eligible, size):
            relevant = [
                pair_map[frozenset((first.camera_id, second.camera_id))]
                for first, second in itertools.combinations(combination, 2)
            ]
            if relevant and all(pair.accepted for pair in relevant):
                compatible_groups.append(
                    (
                        combination,
                        min(pair.total_score for pair in relevant),
                        sum(pair.total_score for pair in relevant) / len(relevant),
                    )
                )
    best_pair = max(
        pairs,
        key=lambda pair: (
            pair.total_score,
            -int(pair.camera_a.split("_")[-1]),
            -int(pair.camera_b.split("_")[-1]),
        ),
    )
    # Anchor selection on the strongest pair. A larger group is useful only when
    # every additional relationship is high-confidence and remains close to the
    # strongest pair's score; otherwise a merely large clique can absorb weak,
    # coincidental audio matches.
    expandable_groups = [
        item
        for item in compatible_groups
        if item[1] >= best_pair.total_score - GROUP_EXPANSION_SCORE_MARGIN
        and all(
            pair_map[frozenset((first.camera_id, second.camera_id))].confidence
            == "high"
            for first, second in itertools.combinations(item[0], 2)
        )
    ]
    expandable_groups.sort(
        key=lambda item: (
            -len(item[0]),
            -item[1],
            -item[2],
            tuple(video.camera_id or "" for video in item[0]),
        )
    )
    if expandable_groups:
        selected, minimum_score, _ = expandable_groups[0]
        high = all(
            pair_map[frozenset((first.camera_id, second.camera_id))].confidence
            == "high"
            for first, second in itertools.combinations(selected, 2)
        )
        state = (
            CameraGroupingState.CAMERA_GROUP_CONFIRMED
            if high
            else CameraGroupingState.CAMERA_GROUP_SUGGESTED
        )
        confidence = "high" if high else "medium"
        reason = (
            "Selected the deterministic mutually compatible camera group from "
            "pairwise local evidence."
        )
        chosen = selected
        suggested = ()
        best_score = minimum_score
    elif compatible_groups:
        compatible_groups.sort(
            key=lambda item: (
                -item[1],
                -item[2],
                -len(item[0]),
                tuple(video.camera_id or "" for video in item[0]),
            )
        )
        chosen, minimum_score, _ = compatible_groups[0]
        suggested = ()
        state = CameraGroupingState.CAMERA_GROUP_SUGGESTED
        confidence = "medium"
        reason = (
            "Selected the strongest threshold-passing camera group as a "
            "medium-confidence suggestion. Human verification is required before "
            "a normal draft; explicit smoke mode may continue with clear labels."
        )
        best_score = minimum_score
    else:
        physically_possible = [
            pair
            for pair in pairs
            if pair.common_usable_duration_seconds >= minimum_common_duration_seconds
            and pair.derived_duplicate_likelihood < 0.7
        ]
        if physically_possible:
            suggestion_pair = max(
                physically_possible,
                key=lambda pair: (
                    pair.total_score,
                    pair.common_usable_duration_seconds,
                    -int(pair.camera_a.split("_")[-1]),
                    -int(pair.camera_b.split("_")[-1]),
                ),
            )
            by_id = {video.camera_id: video for video in eligible}
            suggested = (
                by_id[suggestion_pair.camera_a],
                by_id[suggestion_pair.camera_b],
            )
            pairs = tuple(
                replace(pair, suggested=pair == suggestion_pair) for pair in pairs
            )
            state = CameraGroupingState.CAMERA_GROUP_LOW_CONFIDENCE
            confidence = "low"
            reason = (
                "No pair met the automatic acceptance thresholds. The highest "
                f"physically usable pair is suggested for human verification: "
                f"{suggestion_pair.camera_a}/{suggestion_pair.camera_b} score "
                f"{suggestion_pair.total_score:.3f}. The operator may continue only "
                "after explicitly accepting or changing this group."
            )
        else:
            suggested = ()
            state = CameraGroupingState.NO_RELIABLE_CAMERA_GROUP
            confidence = "none"
            reason = (
                "No pair has enough physically possible common footage after "
                "invalid and derived inputs are excluded."
            )
        chosen = ()
        best_score = best_pair.total_score
    result = CameraGroupingResult(
        state=state,
        selected_videos=chosen,
        pair_scores=tuple(
            sorted(
                pairs,
                key=lambda pair: (-pair.total_score, pair.camera_a, pair.camera_b),
            )
        ),
        eligible_count=len(eligible),
        excluded_derived_count=excluded_derived,
        analysed_pair_count=len(pairs),
        best_score=round(best_score, 6),
        confidence=confidence,
        reason=reason,
        suggested_videos=suggested,
        report_path=report_path,
    )
    _write_grouping_report(result, report_path)
    return result


def _write_grouping_report(
    result: CameraGroupingResult, report_path: Path | None
) -> None:
    if report_path is None:
        return
    write_json_atomic(
        report_path,
        {
            "generated_at": utc_now(),
            "processing": "local deterministic multi-signal camera grouping",
            "scoring_weights": SCORING_WEIGHTS,
            "thresholds": {
                "pair_acceptance_score": PAIR_ACCEPTANCE_SCORE,
                "high_confidence_score": HIGH_CONFIDENCE_SCORE,
                "group_expansion_score_margin": GROUP_EXPANSION_SCORE_MARGIN,
                "minimum_audio_correlation": MINIMUM_AUDIO_CORRELATION,
            },
            "state": result.state.value,
            "confidence": result.confidence,
            "reason": result.reason,
            "eligible_source_count": result.eligible_count,
            "excluded_derived_count": result.excluded_derived_count,
            "analysed_pair_count": result.analysed_pair_count,
            "best_score": result.best_score,
            "selected_camera_ids": [
                video.camera_id for video in result.selected_videos
            ],
            "selected_paths": [video.relative_path for video in result.selected_videos],
            "suggested_camera_ids": [
                video.camera_id for video in result.suggested_videos
            ],
            "suggested_paths": [
                video.relative_path for video in result.suggested_videos
            ],
            "pairs": [asdict(pair) for pair in result.pair_scores],
            "privacy": {
                "local_audio_only": True,
                "video_frames_decoded": False,
                "biometric_analysis": False,
                "cloud_processing": False,
            },
        },
    )
