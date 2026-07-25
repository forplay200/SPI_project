from __future__ import annotations

import unittest
from pathlib import Path

from src.errors import SyncValidationError
from src.models import CameraSource, SyncConfig
from src.sync import apply_sync, calculate_offsets, parse_sync_config


class SyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cameras = (
            CameraSource("master", Path("master.mp4")),
            CameraSource("late", Path("late.mp4")),
            CameraSource("early", Path("early.mp4")),
        )

    def test_positive_zero_and_negative_offsets(self) -> None:
        sync = SyncConfig(
            master_camera="master",
            clap_timestamps={"master": 5.0, "late": 7.2, "early": 4.25},
        )
        offsets = calculate_offsets(self.cameras, sync, expected_master_camera="master")
        self.assertEqual(offsets, {"master": 0.0, "late": 2.2, "early": -0.75})
        synced = apply_sync(self.cameras, sync, expected_master_camera="master")
        self.assertEqual(synced[1].clap_time_seconds, 7.2)

    def test_missing_timestamp_is_actionable(self) -> None:
        sync = SyncConfig(
            master_camera="master", clap_timestamps={"master": 5.0, "late": 7.2}
        )
        with self.assertRaises(SyncValidationError) as raised:
            calculate_offsets(self.cameras, sync, expected_master_camera="master")
        self.assertIn("early", str(raised.exception))

    def test_preserves_non_clap_cue_status_for_honest_evidence(self) -> None:
        config = parse_sync_config(
            {
                "master_camera": "master",
                "clap_timestamps": {"master": 5.0},
                "cue_type": "shared_audio_transient_unconfirmed_as_clap",
                "cue_description": "Measured landmark; manual review required.",
                "acceptance_status": "manual_clap_review_required",
            }
        )
        self.assertEqual(config.cue_type, "shared_audio_transient_unconfirmed_as_clap")
        self.assertEqual(config.acceptance_status, "manual_clap_review_required")


if __name__ == "__main__":
    unittest.main()
