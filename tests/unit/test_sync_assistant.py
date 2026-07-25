from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from src.models import CameraSource
from src.sync_assistant import (
    SAMPLE_RATE,
    analyse_camera_audio,
    analyse_sync,
    confirm_sync_timestamp,
    detect_transient_candidates,
)


def pulse_audio(timestamp: float, *, duration: float = 3.0) -> np.ndarray:
    samples = np.zeros(round(duration * SAMPLE_RATE), dtype=np.float32)
    start = round(timestamp * SAMPLE_RATE)
    samples[start : start + round(0.02 * SAMPLE_RATE)] = 1.0
    return samples


class SyncAssistantTests(unittest.TestCase):
    def test_clear_synthetic_transient_and_offset_are_deterministic(self) -> None:
        first = detect_transient_candidates(pulse_audio(0.8))
        repeated = detect_transient_candidates(pulse_audio(0.8))
        late = detect_transient_candidates(pulse_audio(1.1))
        self.assertEqual(first, repeated)
        self.assertAlmostEqual(first[0].timestamp_seconds, 0.81, delta=0.03)
        self.assertAlmostEqual(
            late[0].timestamp_seconds - first[0].timestamp_seconds, 0.3, delta=0.03
        )
        self.assertGreaterEqual(first[0].confidence, 0.65)

    def test_multi_camera_analysis_recovers_known_offset(self) -> None:
        cameras = (
            CameraSource("camera_01", Path("a.mp4"), has_audio=True),
            CameraSource("camera_02", Path("b.mp4"), has_audio=True),
        )

        def decoded(path: Path, **_: object) -> np.ndarray:
            return pulse_audio(0.8 if path.name == "a.mp4" else 1.1)

        with patch("src.sync_assistant.decode_audio_window", side_effect=decoded):
            analyses, payload = analyse_sync(cameras, master_camera="camera_01")
        timestamps = payload["clap_timestamps"]
        self.assertEqual(len(analyses), 2)
        self.assertAlmostEqual(
            timestamps["camera_02"] - timestamps["camera_01"],  # type: ignore[index]
            0.3,
            delta=0.03,
        )
        self.assertEqual(payload["acceptance_status"], "needs_human_confirmation")

    def test_low_confidence_audio_does_not_invent_timestamp(self) -> None:
        samples = np.full(SAMPLE_RATE * 2, 0.01, dtype=np.float32)
        camera = CameraSource("camera_01", Path("a.mp4"), has_audio=True)
        with patch("src.sync_assistant.decode_audio_window", return_value=samples):
            analysis = analyse_camera_audio(camera)
        self.assertIsNone(analysis.selected_timestamp_seconds)
        self.assertEqual(analysis.state, "no_reliable_candidate")

    def test_no_audio_has_no_candidate(self) -> None:
        analysis = analyse_camera_audio(
            CameraSource("camera_01", Path("silent.mp4"), has_audio=False)
        )
        self.assertEqual(analysis.candidates, ())
        self.assertIsNone(analysis.selected_timestamp_seconds)

    def test_multiple_transients_are_ranked(self) -> None:
        samples = pulse_audio(0.5)
        start = round(1.5 * SAMPLE_RATE)
        samples[start : start + round(0.02 * SAMPLE_RATE)] = 0.7
        candidates = detect_transient_candidates(samples)
        self.assertGreaterEqual(len(candidates), 2)
        self.assertLess(
            candidates[0].timestamp_seconds, candidates[1].timestamp_seconds
        )

    def test_manual_confirmation_requires_every_camera_for_verified_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "generated_sync.json"
            path.write_text(
                json.dumps(
                    {
                        "master_camera": "camera_01",
                        "clap_timestamps": {},
                        "camera_analyses": [
                            {"camera_id": "camera_01"},
                            {"camera_id": "camera_02"},
                        ],
                        "manual_confirmations": {},
                    }
                ),
                encoding="utf-8",
            )
            partial = confirm_sync_timestamp(
                path, camera_id="camera_01", timestamp_seconds=1.25
            )
            self.assertEqual(partial["acceptance_status"], "needs_human_confirmation")
            complete = confirm_sync_timestamp(
                path, camera_id="camera_02", timestamp_seconds=1.55
            )
            self.assertEqual(complete["acceptance_status"], "verified")
            self.assertEqual(complete["cue_type"], "manual_clap")


if __name__ == "__main__":
    unittest.main()
