"""Local deterministic audio cue detection for manual sync assistance."""

from __future__ import annotations

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
        samples = decode_audio_window(
            camera.path,
            search_window_seconds=search_window_seconds,
            ffmpeg_executable=ffmpeg_executable,
        )
        samples_by_camera[camera.id] = samples
        candidates = detect_transient_candidates(samples)
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
    timestamps = {
        item.camera_id: item.selected_timestamp_seconds
        for item in analyses
        if item.selected_timestamp_seconds is not None
    }
    complete = len(timestamps) == len(cameras)
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
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "camera_analyses": [asdict(item) for item in analyses],
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
) -> dict[str, object]:
    if timestamp_seconds < 0:
        raise PreparationError("A confirmed sync timestamp cannot be negative.")
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
    timestamps = payload.get("clap_timestamps")
    if not isinstance(timestamps, dict):
        timestamps = {}
    timestamps[camera_id] = round(float(timestamp_seconds), 6)
    confirmations = payload.get("manual_confirmations")
    if not isinstance(confirmations, dict):
        confirmations = {}
    confirmations[camera_id] = {
        "timestamp_seconds": round(float(timestamp_seconds), 6),
        "state": "manually_verified_clap",
        "confirmed_at": utc_now(),
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
    write_json_atomic(sync_path, payload)
    return payload
