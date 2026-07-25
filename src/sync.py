"""Manual clap synchronisation and constant-offset calculation."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path
from typing import Any

from .errors import ConfigurationError, SyncValidationError
from .json_utils import read_json_object
from .models import CameraSource, SyncConfig


def parse_sync_config(data: dict[str, Any]) -> SyncConfig:
    errors: list[str] = []
    master = data.get("master_camera")
    if not isinstance(master, str) or not master.strip():
        errors.append("master_camera must be a non-empty string.")
        master = ""
    clap_data = data.get("clap_timestamps")
    clap_timestamps: dict[str, float] = {}
    if not isinstance(clap_data, dict):
        errors.append("clap_timestamps must be an object keyed by camera ID.")
    else:
        for camera_id, raw_time in clap_data.items():
            if not isinstance(camera_id, str) or not camera_id.strip():
                errors.append(
                    "Every clap_timestamps key must be a non-empty camera ID."
                )
                continue
            if isinstance(raw_time, bool) or not isinstance(raw_time, (int, float)):
                errors.append(f"Clap timestamp for {camera_id!r} must be numeric.")
            elif raw_time < 0:
                errors.append(f"Clap timestamp for {camera_id!r} cannot be negative.")
            else:
                clap_timestamps[camera_id] = float(raw_time)
    threshold = data.get("verification_threshold_ms", 100)
    if isinstance(threshold, bool) or not isinstance(threshold, int) or threshold <= 0:
        errors.append("verification_threshold_ms must be a positive integer.")
        threshold = 100
    cue_type = data.get("cue_type", "manual_clap")
    if not isinstance(cue_type, str) or not cue_type.strip():
        errors.append("cue_type must be a non-empty string when provided.")
        cue_type = "manual_clap"
    cue_description = data.get("cue_description")
    if cue_description is not None and (
        not isinstance(cue_description, str) or not cue_description.strip()
    ):
        errors.append("cue_description must be a non-empty string when provided.")
        cue_description = None
    acceptance_status = data.get("acceptance_status", "verified")
    if not isinstance(acceptance_status, str) or not acceptance_status.strip():
        errors.append("acceptance_status must be a non-empty string when provided.")
        acceptance_status = "verified"
    if errors:
        raise ConfigurationError(
            "Synchronisation configuration errors:\n- " + "\n- ".join(errors)
        )
    return SyncConfig(
        master_camera=master.strip(),
        clap_timestamps=clap_timestamps,
        verification_threshold_ms=threshold,
        cue_type=cue_type.strip(),
        cue_description=cue_description.strip() if cue_description else None,
        acceptance_status=acceptance_status.strip(),
    )


def load_sync_config(path: Path) -> SyncConfig:
    return parse_sync_config(
        read_json_object(path.resolve(), label="Synchronisation configuration")
    )


def calculate_offsets(
    cameras: Iterable[CameraSource],
    sync_config: SyncConfig,
    *,
    expected_master_camera: str,
) -> dict[str, float]:
    """Calculate `camera clap - master clap` for all configured cameras."""
    camera_ids = [camera.id for camera in cameras]
    errors: list[str] = []
    if sync_config.master_camera != expected_master_camera:
        errors.append(
            f"sync master_camera {sync_config.master_camera!r} does not match project "
            f"master_camera {expected_master_camera!r}."
        )
    missing = sorted(set(camera_ids) - set(sync_config.clap_timestamps))
    unknown = sorted(set(sync_config.clap_timestamps) - set(camera_ids))
    if missing:
        errors.append(f"Missing clap timestamps for cameras: {missing}.")
    if unknown:
        errors.append(f"Clap timestamps reference unknown cameras: {unknown}.")
    if expected_master_camera not in sync_config.clap_timestamps:
        errors.append(
            f"Master camera {expected_master_camera!r} has no clap timestamp."
        )
    if errors:
        raise SyncValidationError("Synchronisation errors:\n- " + "\n- ".join(errors))
    master_time = sync_config.clap_timestamps[expected_master_camera]
    offsets = {
        camera_id: round(sync_config.clap_timestamps[camera_id] - master_time, 6)
        for camera_id in camera_ids
    }
    if offsets[expected_master_camera] != 0:
        raise SyncValidationError("Master camera offset did not resolve to zero.")
    return offsets


def apply_sync(
    cameras: Iterable[CameraSource],
    sync_config: SyncConfig,
    *,
    expected_master_camera: str,
) -> tuple[CameraSource, ...]:
    cameras_tuple = tuple(cameras)
    offsets = calculate_offsets(
        cameras_tuple, sync_config, expected_master_camera=expected_master_camera
    )
    return tuple(
        replace(
            camera,
            clap_time_seconds=sync_config.clap_timestamps[camera.id],
            offset_seconds=offsets[camera.id],
        )
        for camera in cameras_tuple
    )
