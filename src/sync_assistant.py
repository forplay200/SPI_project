"""Local deterministic audio cue detection for manual sync assistance."""

from __future__ import annotations

import itertools
import math
import subprocess
from dataclasses import asdict
from pathlib import Path

import numpy as np

from .errors import PreparationError
from .evidence import utc_now
from .json_utils import read_json_object, write_generated_json, write_json_atomic
from .models import CameraSource, CameraSyncAnalysis, SyncCandidate
from .preflight import resolve_executable

SAMPLE_RATE = 8000
FRAME_SECONDS = 0.02
CONFIDENCE_THRESHOLD = 0.65
DEFAULT_ALIGNMENT_WINDOW_SECONDS = 120.0
MAXIMUM_ALIGNMENT_OFFSET_SECONDS = 60.0
LARGE_OFFSET_THRESHOLD_SECONDS = 10.0
MINIMUM_ALIGNMENT_OVERLAP_RATIO = 0.60
MINIMUM_ALIGNMENT_CORRELATION = 0.55
LARGE_OFFSET_MINIMUM_CORRELATION = 0.70
LARGE_OFFSET_MINIMUM_STABILITY = 0.80


def decode_audio_window(
    path: Path,
    *,
    search_window_seconds: float = 15.0,
    ffmpeg_executable: str | Path | None = None,
) -> np.ndarray:
    executable = (
        str(ffmpeg_executable)
        if ffmpeg_executable is not None
        else resolve_executable("ffmpeg")
    )
    if not executable:
        raise PreparationError(
            "FFmpeg is required for local audio cue analysis. Install it or pass "
            "--ffmpeg with an executable path."
        )
    command = [
        executable,
        "-hide_banner",
        "-loglevel",
        "error",
        "-t",
        f"{search_window_seconds:.6f}",
        "-i",
        str(path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(SAMPLE_RATE),
        "-f",
        "f32le",
        "pipe:1",
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            shell=False,
            timeout=max(30, int(search_window_seconds * 4)),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise PreparationError(
            f"Could not decode local audio from {path}: {exc}"
        ) from exc
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()[-1000:]
        raise PreparationError(
            f"FFmpeg could not decode local audio from {path}: {detail}"
        )
    return np.frombuffer(completed.stdout, dtype="<f4").copy()


def detect_transient_candidates(
    samples: np.ndarray,
    *,
    max_candidates: int = 5,
) -> tuple[SyncCandidate, ...]:
    """Rank transient energy peaks; return no timestamp when the signal is weak."""
    frame_size = max(1, round(SAMPLE_RATE * FRAME_SECONDS))
    usable = len(samples) - (len(samples) % frame_size)
    if usable < frame_size * 3:
        return ()
    frames = samples[:usable].reshape(-1, frame_size)
    envelope = np.sqrt(np.mean(np.square(frames, dtype=np.float64), axis=1))
    median = float(np.median(envelope))
    mad = float(np.median(np.abs(envelope - median)))
    scale = max(mad * 1.4826, median * 0.02, 1e-7)
    prominence = (envelope - median) / scale
    indices = [
        index
        for index in range(1, len(envelope) - 1)
        if prominence[index] >= 4.0
        and envelope[index] >= envelope[index - 1]
        and envelope[index] > envelope[index + 1]
    ]
    indices.sort(key=lambda index: (-float(prominence[index]), index))
    selected: list[int] = []
    minimum_gap = round(0.25 / FRAME_SECONDS)
    for index in indices:
        if all(abs(index - prior) >= minimum_gap for prior in selected):
            selected.append(index)
        if len(selected) >= max_candidates:
            break
    candidates: list[SyncCandidate] = []
    for index in selected:
        metric = float(prominence[index])
        confidence = max(0.0, min(0.99, (metric - 4.0) / 12.0))
        cue_type = (
            "clap_candidate"
            if confidence >= CONFIDENCE_THRESHOLD
            else "low_confidence_candidate"
        )
        candidates.append(
            SyncCandidate(
                timestamp_seconds=round((index + 0.5) * FRAME_SECONDS, 3),
                confidence=round(confidence, 3),
                cue_type=cue_type,
                supporting_metric=round(metric, 3),
            )
        )
    return tuple(candidates)


def _energy_envelope(samples: np.ndarray) -> np.ndarray:
    frame_size = max(1, round(SAMPLE_RATE * FRAME_SECONDS))
    usable = len(samples) - (len(samples) % frame_size)
    if usable < frame_size * 3:
        return np.array([], dtype=np.float64)
    frames = samples[:usable].reshape(-1, frame_size)
    return np.sqrt(np.mean(np.square(frames, dtype=np.float64), axis=1))


def audio_energy_envelope(samples: np.ndarray) -> np.ndarray:
    """Return the grouping/sync RMS envelope for already-decoded mono audio."""
    return _energy_envelope(samples)


def _best_envelope_lag(
    master: np.ndarray, other: np.ndarray, *, maximum_lag_seconds: float = 3.0
) -> tuple[int, float]:
    master_centered = master - np.mean(master)
    other_centered = other - np.mean(other)
    full = np.correlate(other_centered, master_centered, mode="full")
    lags = np.arange(-len(master_centered) + 1, len(other_centered))
    maximum_lag = round(maximum_lag_seconds / FRAME_SECONDS)
    mask = np.abs(lags) <= maximum_lag
    limited_indices = np.flatnonzero(mask)
    if not len(limited_indices):
        return 0, 0.0
    best_index = int(limited_indices[np.argmax(full[mask])])
    lag = int(lags[best_index])
    if lag >= 0:
        master_overlap = master_centered[: min(len(master), len(other) - lag)]
        other_overlap = other_centered[lag : lag + len(master_overlap)]
    else:
        master_overlap = master_centered[
            -lag : -lag + min(len(master) + lag, len(other))
        ]
        other_overlap = other_centered[: len(master_overlap)]
    denominator = float(np.linalg.norm(master_overlap) * np.linalg.norm(other_overlap))
    correlation = (
        float(np.dot(master_overlap, other_overlap) / denominator)
        if denominator > 0 and len(master_overlap)
        else 0.0
    )
    return lag, max(-1.0, min(1.0, correlation))


def estimate_envelope_offset(
    master: np.ndarray,
    other: np.ndarray,
    *,
    maximum_offset_seconds: float = 5.0,
) -> tuple[float, float]:
    """Estimate `other - master` offset and normalized envelope correlation."""
    lag, correlation = _best_envelope_lag(
        master,
        other,
        maximum_lag_seconds=maximum_offset_seconds,
    )
    return round(lag * FRAME_SECONDS, 6), correlation


def _normalized_envelope(samples: np.ndarray) -> np.ndarray:
    envelope = _energy_envelope(samples)
    positive = envelope[envelope > 0]
    scale = float(np.median(positive)) if len(positive) else 1.0
    return np.log1p(envelope / max(scale, 1e-8))


def _aligned_envelopes(
    master: np.ndarray, other: np.ndarray, lag: int
) -> tuple[np.ndarray, np.ndarray]:
    if lag >= 0:
        length = min(len(master), len(other) - lag)
        return master[: max(0, length)], other[lag : lag + max(0, length)]
    length = min(len(master) + lag, len(other))
    return master[-lag : -lag + max(0, length)], other[: max(0, length)]


def _correlation_at_lag(
    master: np.ndarray, other: np.ndarray, lag: int
) -> tuple[float, int]:
    first, second = _aligned_envelopes(master, other, lag)
    if len(first) < 3:
        return 0.0, len(first)
    first = first - np.mean(first)
    second = second - np.mean(second)
    denominator = float(np.linalg.norm(first) * np.linalg.norm(second))
    correlation = float(np.dot(first, second) / denominator) if denominator else 0.0
    return max(-1.0, min(1.0, correlation)), len(first)


def rank_alignment_offsets(
    master_samples: np.ndarray,
    other_samples: np.ndarray,
    *,
    maximum_offset_seconds: float = MAXIMUM_ALIGNMENT_OFFSET_SECONDS,
    max_candidates: int = 5,
) -> tuple[dict[str, object], ...]:
    """Rank offset alternatives with overlap and multi-window sanity evidence."""
    master = _normalized_envelope(master_samples)
    other = _normalized_envelope(other_samples)
    shortest = min(len(master), len(other))
    if shortest < round(2.0 / FRAME_SECONDS):
        return ()
    maximum_lag = min(
        round(maximum_offset_seconds / FRAME_SECONDS),
        len(master) - 3,
        len(other) - 3,
    )
    minimum_overlap = max(
        round(2.0 / FRAME_SECONDS),
        math.ceil(shortest * MINIMUM_ALIGNMENT_OVERLAP_RATIO),
    )
    ranked: list[tuple[float, int, float, float]] = []
    for lag in range(-maximum_lag, maximum_lag + 1):
        correlation, overlap_frames = _correlation_at_lag(master, other, lag)
        if overlap_frames < minimum_overlap:
            continue
        overlap_ratio = overlap_frames / shortest
        overlap_weighted_score = max(0.0, correlation) * math.sqrt(overlap_ratio)
        ranked.append((overlap_weighted_score, lag, correlation, overlap_ratio))
    ranked.sort(key=lambda item: (-item[0], -item[3], abs(item[1]), item[1]))
    separated: list[tuple[float, int, float, float]] = []
    separation_frames = max(1, round(0.5 / FRAME_SECONDS))
    for item in ranked:
        if all(abs(item[1] - prior[1]) >= separation_frames for prior in separated):
            separated.append(item)
        if len(separated) >= max_candidates:
            break

    alternatives: list[dict[str, object]] = []
    for weighted_score, lag, correlation, overlap_ratio in separated:
        aligned_master, aligned_other = _aligned_envelopes(master, other, lag)
        overlap_frames = len(aligned_master)
        window_frames = min(
            round(15.0 / FRAME_SECONDS),
            max(1, overlap_frames // 3),
        )
        positions = tuple(
            dict.fromkeys(
                (
                    0,
                    max(0, (overlap_frames - window_frames) // 2),
                    max(0, overlap_frames - window_frames),
                )
            )
        )
        window_offsets: list[float] = []
        window_correlations: list[float] = []
        for start in positions:
            first_window = aligned_master[start : start + window_frames]
            second_window = aligned_other[start : start + window_frames]
            adjustment, window_correlation = estimate_envelope_offset(
                first_window,
                second_window,
                maximum_offset_seconds=1.0,
            )
            window_offsets.append(lag * FRAME_SECONDS + adjustment)
            window_correlations.append(max(0.0, window_correlation))
        supported_offsets = [
            offset
            for offset, value in zip(window_offsets, window_correlations)
            if value >= 0.25
        ]
        supported_windows = len(supported_offsets)
        if supported_windows >= 2:
            spread = float(np.std(supported_offsets))
            stability = max(0.0, min(1.0, 1.0 - spread / 0.5))
            stability *= supported_windows / max(1, len(window_offsets))
        else:
            stability = 0.0
        median_window_correlation = (
            float(np.median(window_correlations)) if window_correlations else 0.0
        )
        offset_seconds = lag * FRAME_SECONDS
        large_offset = abs(offset_seconds) > LARGE_OFFSET_THRESHOLD_SECONDS
        confidence = (
            max(0.0, correlation) * 0.45
            + median_window_correlation * 0.25
            + stability * 0.20
            + overlap_ratio * 0.10
        )
        accepted = (
            correlation >= MINIMUM_ALIGNMENT_CORRELATION
            and median_window_correlation >= 0.25
            and supported_windows >= 2
            and stability >= 0.55
            and overlap_ratio >= MINIMUM_ALIGNMENT_OVERLAP_RATIO
        )
        if large_offset:
            accepted = (
                accepted
                and correlation >= LARGE_OFFSET_MINIMUM_CORRELATION
                and stability >= LARGE_OFFSET_MINIMUM_STABILITY
                and supported_windows == len(window_offsets)
                and overlap_ratio >= 0.75
            )
        if accepted:
            reason = (
                "Accepted as an offset suggestion from stable multi-window audio "
                "alignment; the cue still requires human verification."
            )
        elif large_offset and correlation < LARGE_OFFSET_MINIMUM_CORRELATION:
            reason = (
                "Rejected for automatic use because a large offset needs stronger "
                "audio correlation."
            )
        elif large_offset and stability < LARGE_OFFSET_MINIMUM_STABILITY:
            reason = (
                "Rejected for automatic use because a large offset was not stable "
                "across every analysed window."
            )
        elif supported_windows < 2:
            reason = (
                "Rejected for automatic use because fewer than two audio windows "
                "support the same offset."
            )
        elif correlation < MINIMUM_ALIGNMENT_CORRELATION:
            reason = "Rejected for automatic use because audio correlation is weak."
        else:
            reason = (
                "Rejected for automatic use because the combined stability and "
                "overlap evidence is insufficient."
            )
        alternatives.append(
            {
                "offset_seconds": round(offset_seconds, 6),
                "confidence": round(max(0.0, min(1.0, confidence)), 6),
                "audio_correlation": round(correlation, 6),
                "overlap_weighted_score": round(weighted_score, 6),
                "overlap_seconds": round(overlap_frames * FRAME_SECONDS, 6),
                "overlap_ratio": round(overlap_ratio, 6),
                "offset_stability": round(stability, 6),
                "supported_windows": supported_windows,
                "window_offsets_seconds": [round(value, 6) for value in window_offsets],
                "window_correlations": [
                    round(value, 6) for value in window_correlations
                ],
                "large_offset": large_offset,
                "accepted_for_automatic_use": accepted,
                "reason": reason,
            }
        )
    return tuple(alternatives)


def calculate_sync_sanity(
    cameras: tuple[CameraSource, ...],
    *,
    master_camera: str,
    timestamps: dict[str, float],
    large_offset_threshold_seconds: float = LARGE_OFFSET_THRESHOLD_SECONDS,
) -> dict[str, object]:
    """Explain offset arithmetic and its impact on common usable footage."""
    by_id = {camera.id: camera for camera in cameras}
    master_timestamp = timestamps.get(master_camera)
    available_ids = [camera.id for camera in cameras if camera.id in timestamps]
    if master_timestamp is None or len(available_ids) < 2:
        return {
            "status": "INCOMPLETE",
            "offset_formula": "camera timestamp - master timestamp",
            "offsets_seconds": {},
            "common_usable_duration_seconds": None,
            "zero_offset_common_duration_seconds": None,
            "overlap_preservation_ratio": None,
            "warnings": [],
        }
    offsets = {
        camera_id: round(timestamps[camera_id] - master_timestamp, 6)
        for camera_id in available_ids
    }
    cameras_with_duration = [
        by_id[camera_id]
        for camera_id in available_ids
        if by_id[camera_id].duration_seconds is not None
    ]
    zero_common = (
        min(float(camera.duration_seconds) for camera in cameras_with_duration)
        if len(cameras_with_duration) == len(available_ids)
        else None
    )
    common_duration: float | None = None
    common_start: float | None = None
    common_end: float | None = None
    if zero_common is not None:
        common_start = max(
            max(0.0, -offsets[camera.id]) for camera in cameras_with_duration
        )
        common_end = min(
            float(camera.duration_seconds) - offsets[camera.id]
            for camera in cameras_with_duration
        )
        common_duration = max(0.0, common_end - common_start)
    preservation = (
        common_duration / zero_common
        if common_duration is not None and zero_common and zero_common > 0
        else None
    )
    warnings = [
        (
            f"{camera_id} offset {offset:+.3f}s exceeds the configured "
            f"{large_offset_threshold_seconds:.3f}s large-offset threshold."
        )
        for camera_id, offset in offsets.items()
        if camera_id != master_camera and abs(offset) > large_offset_threshold_seconds
    ]
    if preservation is not None and preservation < 0.70:
        warnings.append(
            "The proposed timestamps preserve only "
            f"{preservation * 100:.1f}% of the zero-offset common footage "
            f"({common_duration:.3f}s versus {zero_common:.3f}s)."
        )
    status = "WARNING" if warnings else "PLAUSIBLE"
    return {
        "status": status,
        "offset_formula": "camera timestamp - master timestamp",
        "master_camera": master_camera,
        "master_timestamp_seconds": round(master_timestamp, 6),
        "offsets_seconds": offsets,
        "common_timeline_start_seconds": (
            round(common_start, 6) if common_start is not None else None
        ),
        "common_timeline_end_seconds": (
            round(common_end, 6) if common_end is not None else None
        ),
        "common_usable_duration_seconds": (
            round(common_duration, 6) if common_duration is not None else None
        ),
        "zero_offset_common_duration_seconds": (
            round(zero_common, 6) if zero_common is not None else None
        ),
        "overlap_preservation_ratio": (
            round(preservation, 6) if preservation is not None else None
        ),
        "large_offset_threshold_seconds": large_offset_threshold_seconds,
        "warnings": warnings,
    }


def _shared_anchor(master: np.ndarray, other: np.ndarray, lag: int) -> tuple[int, int]:
    if lag >= 0:
        length = min(len(master), len(other) - lag)
        master_start, other_start = 0, lag
    else:
        length = min(len(master) + lag, len(other))
        master_start, other_start = -lag, 0
    master_slice = master[master_start : master_start + length]
    other_slice = other[other_start : other_start + length]
    master_scale = max(float(np.std(master_slice)), 1e-9)
    other_scale = max(float(np.std(other_slice)), 1e-9)
    master_positive = np.maximum(
        0.0, (master_slice - np.median(master_slice)) / master_scale
    )
    other_positive = np.maximum(
        0.0, (other_slice - np.median(other_slice)) / other_scale
    )
    local_index = int(np.argmax(master_positive * other_positive))
    return master_start + local_index, other_start + local_index


def analyse_camera_audio(
    camera: CameraSource,
    *,
    search_window_seconds: float = 15.0,
    ffmpeg_executable: str | Path | None = None,
) -> CameraSyncAnalysis:
    if camera.has_audio is False:
        return CameraSyncAnalysis(
            camera_id=camera.id,
            candidates=(),
            selected_timestamp_seconds=None,
            confidence=0.0,
            state="no_reliable_candidate",
            requires_human_verification=True,
            warnings=("Camera has no audio stream.",),
        )
    samples = decode_audio_window(
        camera.path,
        search_window_seconds=search_window_seconds,
        ffmpeg_executable=ffmpeg_executable,
    )
    candidates = detect_transient_candidates(samples)
    strongest = candidates[0] if candidates else None
    reliable = strongest is not None and strongest.confidence >= CONFIDENCE_THRESHOLD
    state = (
        "shared_audio_transient"
        if reliable
        else ("low_confidence_candidate" if strongest else "no_reliable_candidate")
    )
    warning = (
        ()
        if reliable
        else (
            (
                "No transient exceeded the documented confidence threshold; no "
                "canonical timestamp was selected."
            ),
        )
    )
    return CameraSyncAnalysis(
        camera_id=camera.id,
        candidates=candidates,
        selected_timestamp_seconds=(
            strongest.timestamp_seconds if reliable and strongest else None
        ),
        confidence=strongest.confidence if strongest else 0.0,
        state=state,
        requires_human_verification=True,
        warnings=warning,
    )


def analyse_sync(
    cameras: tuple[CameraSource, ...],
    *,
    master_camera: str,
    search_window_seconds: float = 15.0,
    alignment_window_seconds: float = DEFAULT_ALIGNMENT_WINDOW_SECONDS,
    ffmpeg_executable: str | Path | None = None,
    sync_path: Path | None = None,
    report_path: Path | None = None,
    overwrite: bool = False,
) -> tuple[tuple[CameraSyncAnalysis, ...], dict[str, object]]:
    samples_by_camera: dict[str, np.ndarray] = {}
    analysis_items: list[CameraSyncAnalysis] = []
    for camera in cameras:
        if camera.has_audio is False:
            analysis_items.append(analyse_camera_audio(camera))
            continue
        decode_seconds = min(
            max(search_window_seconds, alignment_window_seconds),
            camera.duration_seconds
            if camera.duration_seconds is not None
            else max(search_window_seconds, alignment_window_seconds),
        )
        samples = decode_audio_window(
            camera.path,
            search_window_seconds=decode_seconds,
            ffmpeg_executable=ffmpeg_executable,
        )
        samples_by_camera[camera.id] = samples
        search_sample_count = round(search_window_seconds * SAMPLE_RATE)
        candidates = detect_transient_candidates(samples[:search_sample_count])
        strongest = candidates[0] if candidates else None
        reliable = (
            strongest is not None and strongest.confidence >= CONFIDENCE_THRESHOLD
        )
        analysis_items.append(
            CameraSyncAnalysis(
                camera_id=camera.id,
                candidates=candidates,
                selected_timestamp_seconds=(
                    strongest.timestamp_seconds if reliable else None
                ),
                confidence=strongest.confidence if strongest else 0.0,
                state=(
                    "shared_audio_transient"
                    if reliable
                    else (
                        "low_confidence_candidate"
                        if strongest
                        else "no_reliable_candidate"
                    )
                ),
                requires_human_verification=True,
                warnings=(
                    ()
                    if reliable
                    else (
                        (
                            "Individual transient prominence is below threshold; "
                            "cross-camera correlation will also be evaluated."
                        ),
                    )
                ),
            )
        )
    analyses = tuple(analysis_items)
    pairwise_alignment: list[dict[str, object]] = []
    for first, second in itertools.combinations(cameras, 2):
        first_samples = samples_by_camera.get(first.id)
        second_samples = samples_by_camera.get(second.id)
        if first_samples is None or second_samples is None:
            pairwise_alignment.append(
                {
                    "camera_a": first.id,
                    "camera_b": second.id,
                    "state": "NO_AUDIO_ALIGNMENT",
                    "selected_offset_seconds": None,
                    "alternatives": [],
                    "reason": "Both cameras need usable audio for offset analysis.",
                }
            )
            continue
        alternatives = rank_alignment_offsets(first_samples, second_samples)
        selected = next(
            (
                item
                for item in alternatives
                if item["accepted_for_automatic_use"] is True
            ),
            None,
        )
        anchor_timestamps: dict[str, float] | None = None
        if selected is not None:
            first_envelope = _energy_envelope(first_samples)
            second_envelope = _energy_envelope(second_samples)
            lag = round(float(selected["offset_seconds"]) / FRAME_SECONDS)
            first_anchor, second_anchor = _shared_anchor(
                first_envelope,
                second_envelope,
                lag,
            )
            anchor_timestamps = {
                first.id: round((first_anchor + 0.5) * FRAME_SECONDS, 3),
                second.id: round((second_anchor + 0.5) * FRAME_SECONDS, 3),
            }
        pairwise_alignment.append(
            {
                "camera_a": first.id,
                "camera_b": second.id,
                "state": (
                    "STABLE_OFFSET_SUGGESTION"
                    if selected is not None
                    else "NEEDS_HUMAN_VERIFICATION"
                ),
                "selected_offset_seconds": (
                    selected["offset_seconds"] if selected is not None else None
                ),
                "shared_anchor_timestamps": anchor_timestamps,
                "alternatives": list(alternatives),
                "reason": (
                    str(selected["reason"])
                    if selected is not None
                    else (
                        "No alternative met the multi-window, overlap, and "
                        "large-offset safety policy."
                    )
                ),
            }
        )

    master_samples = samples_by_camera.get(master_camera)
    if master_samples is not None and len(samples_by_camera) >= 2:
        envelopes = {
            camera_id: _energy_envelope(samples)
            for camera_id, samples in samples_by_camera.items()
        }
        reference_id = next(
            camera.id
            for camera in cameras
            if camera.id != master_camera and camera.id in envelopes
        )
        reference_lag, reference_correlation = _best_envelope_lag(
            envelopes[master_camera], envelopes[reference_id]
        )
        if reference_correlation >= CONFIDENCE_THRESHOLD:
            master_anchor, _ = _shared_anchor(
                envelopes[master_camera],
                envelopes[reference_id],
                reference_lag,
            )
            replacements: list[CameraSyncAnalysis] = []
            for item in analyses:
                if item.camera_id not in envelopes:
                    replacements.append(item)
                    continue
                if item.camera_id == master_camera:
                    lag, correlation = 0, reference_correlation
                else:
                    lag, correlation = _best_envelope_lag(
                        envelopes[master_camera], envelopes[item.camera_id]
                    )
                timestamp = (master_anchor + lag + 0.5) * FRAME_SECONDS
                if (
                    correlation >= CONFIDENCE_THRESHOLD
                    and timestamp >= 0
                    and timestamp <= search_window_seconds
                ):
                    cross_candidate = SyncCandidate(
                        timestamp_seconds=round(timestamp, 3),
                        confidence=round(correlation, 3),
                        cue_type="shared_audio_transient",
                        supporting_metric=round(correlation, 3),
                    )
                    replacements.append(
                        CameraSyncAnalysis(
                            camera_id=item.camera_id,
                            candidates=(cross_candidate,) + item.candidates,
                            selected_timestamp_seconds=(
                                cross_candidate.timestamp_seconds
                            ),
                            confidence=cross_candidate.confidence,
                            state="shared_audio_transient",
                            requires_human_verification=True,
                            warnings=(
                                (
                                    "Cross-camera envelope correlation supports this "
                                    "shared transient, but it is not a verified clap."
                                ),
                            ),
                        )
                    )
                else:
                    replacements.append(item)
            analyses = tuple(replacements)
    if len(cameras) == 2 and pairwise_alignment:
        stable_pair = pairwise_alignment[0]
        anchors = stable_pair.get("shared_anchor_timestamps")
        alternatives = stable_pair.get("alternatives")
        if (
            stable_pair.get("state") == "STABLE_OFFSET_SUGGESTION"
            and isinstance(anchors, dict)
            and isinstance(alternatives, list)
            and alternatives
        ):
            top = alternatives[0]
            replacements = []
            for item in analyses:
                anchor = anchors.get(item.camera_id)
                if not isinstance(anchor, (int, float)):
                    replacements.append(item)
                    continue
                cross_candidate = SyncCandidate(
                    timestamp_seconds=float(anchor),
                    confidence=round(float(top["confidence"]), 3),
                    cue_type="shared_audio_transient",
                    supporting_metric=round(float(top["audio_correlation"]), 3),
                )
                replacements.append(
                    CameraSyncAnalysis(
                        camera_id=item.camera_id,
                        candidates=(cross_candidate,) + item.candidates,
                        selected_timestamp_seconds=float(anchor),
                        confidence=cross_candidate.confidence,
                        state="shared_audio_transient",
                        requires_human_verification=True,
                        warnings=(
                            (
                                "A stable full-recording audio alignment supplied "
                                "this shared anchor. It is not a verified clap."
                            ),
                        ),
                    )
                )
            analyses = tuple(replacements)
    timestamps = {
        item.camera_id: item.selected_timestamp_seconds
        for item in analyses
        if item.selected_timestamp_seconds is not None
    }
    complete = len(timestamps) == len(cameras)
    sync_sanity = calculate_sync_sanity(
        cameras,
        master_camera=master_camera,
        timestamps={key: float(value) for key, value in timestamps.items()},
    )
    payload: dict[str, object] = {
        "generated_by": "automatic_preparation_layer",
        "master_camera": master_camera,
        "cue_type": ("shared_audio_transient" if complete else "no_reliable_candidate"),
        "cue_description": (
            "Deterministic local transient candidates; every value requires human "
            "verification and is not automatically accepted as a deliberate clap."
        ),
        "acceptance_status": "needs_human_confirmation",
        "clap_timestamps": timestamps,
        "verification_threshold_ms": 100,
        "requires_human_verification": True,
        "search_window_seconds": search_window_seconds,
        "alignment_window_seconds": alignment_window_seconds,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "alignment_policy": {
            "maximum_offset_seconds": MAXIMUM_ALIGNMENT_OFFSET_SECONDS,
            "large_offset_threshold_seconds": LARGE_OFFSET_THRESHOLD_SECONDS,
            "minimum_overlap_ratio": MINIMUM_ALIGNMENT_OVERLAP_RATIO,
            "minimum_audio_correlation": MINIMUM_ALIGNMENT_CORRELATION,
            "large_offset_minimum_correlation": LARGE_OFFSET_MINIMUM_CORRELATION,
            "large_offset_minimum_stability": LARGE_OFFSET_MINIMUM_STABILITY,
        },
        "camera_analyses": [asdict(item) for item in analyses],
        "pairwise_alignment": pairwise_alignment,
        "sync_sanity": sync_sanity,
        "manual_confirmations": {},
    }
    if sync_path is not None:
        write_generated_json(sync_path, payload, overwrite=overwrite)
    if report_path is not None:
        write_json_atomic(
            report_path,
            {
                "generated_at": utc_now(),
                "processing": "local deterministic audio transient analysis",
                **payload,
            },
        )
    return analyses, payload


def confirm_sync_timestamp(
    sync_path: Path,
    *,
    camera_id: str,
    timestamp_seconds: float,
    cameras: tuple[CameraSource, ...] = (),
    acknowledge_risk: bool = False,
) -> dict[str, object]:
    if not math.isfinite(timestamp_seconds) or timestamp_seconds < 0:
        raise PreparationError(
            "A confirmed sync timestamp must be a finite non-negative number."
        )
    payload = read_json_object(sync_path, label="Generated synchronisation")
    analyses = payload.get("camera_analyses")
    camera_ids = (
        {
            item.get("camera_id")
            for item in analyses
            if isinstance(item, dict) and isinstance(item.get("camera_id"), str)
        }
        if isinstance(analyses, list)
        else set()
    )
    if camera_id not in camera_ids:
        raise PreparationError(
            f"Camera {camera_id!r} is not present in the generated sync analysis."
        )
    camera = next((item for item in cameras if item.id == camera_id), None)
    if (
        camera is not None
        and camera.duration_seconds is not None
        and timestamp_seconds > camera.duration_seconds
    ):
        raise PreparationError(
            f"Confirmed timestamp {timestamp_seconds:.3f}s exceeds {camera_id} "
            f"duration {camera.duration_seconds:.3f}s."
        )
    timestamps = payload.get("clap_timestamps")
    if not isinstance(timestamps, dict):
        timestamps = {}
    confirmations = payload.get("manual_confirmations")
    if not isinstance(confirmations, dict):
        confirmations = {}
    tentative_timestamps = {
        str(key): float(item["timestamp_seconds"])
        for key, item in confirmations.items()
        if isinstance(key, str)
        and isinstance(item, dict)
        and isinstance(item.get("timestamp_seconds"), (int, float))
    }
    tentative_timestamps[camera_id] = round(float(timestamp_seconds), 6)
    sanity = (
        calculate_sync_sanity(
            cameras,
            master_camera=str(payload.get("master_camera", "")),
            timestamps=tentative_timestamps,
        )
        if cameras
        else None
    )
    sanity_warnings = (
        list(sanity.get("warnings", [])) if isinstance(sanity, dict) else []
    )
    if sanity_warnings and not acknowledge_risk:
        detail = " ".join(str(item) for item in sanity_warnings)
        raise PreparationError(
            f"The proposed manual cue needs explicit synchronization-risk "
            f"acknowledgement. {detail} Verify that every timestamp identifies the "
            "same audible or visible cue, then acknowledge the warning explicitly."
        )
    timestamps = tentative_timestamps
    confirmations[camera_id] = {
        "timestamp_seconds": round(float(timestamp_seconds), 6),
        "state": "manually_verified_clap",
        "confirmed_at": utc_now(),
        "sync_risk_acknowledged": bool(acknowledge_risk and sanity_warnings),
    }
    payload["clap_timestamps"] = timestamps
    payload["manual_confirmations"] = confirmations
    all_confirmed = camera_ids and camera_ids <= set(confirmations)
    payload["cue_type"] = (
        "manual_clap" if all_confirmed else "partially_verified_manual_clap"
    )
    payload["acceptance_status"] = (
        "verified" if all_confirmed else "needs_human_confirmation"
    )
    payload["requires_human_verification"] = not all_confirmed
    if sanity is not None:
        payload["sync_sanity"] = sanity
        payload["sync_risk_acknowledged"] = bool(acknowledge_risk and sanity_warnings)
    write_json_atomic(sync_path, payload)
    return payload
