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
    calculate_sync_sanity,
    confirm_sync_timestamp,
    detect_transient_candidates,
    rank_alignment_offsets,
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

    def test_offset_ranking_rejects_tiny_overlap_local_maximum(self) -> None:
        generator = np.random.default_rng(17)
        master = generator.normal(0, 0.05, SAMPLE_RATE * 24).astype(np.float32)
        other = generator.normal(0, 0.05, SAMPLE_RATE * 24).astype(np.float32)
        other[-round(0.2 * SAMPLE_RATE) :] = master[: round(0.2 * SAMPLE_RATE)]
        alternatives = rank_alignment_offsets(master, other, maximum_offset_seconds=23)
        self.assertTrue(alternatives)
        self.assertTrue(
            all(float(item["overlap_ratio"]) >= 0.6 for item in alternatives)
        )
        self.assertTrue(
            all(abs(float(item["offset_seconds"])) < 10 for item in alternatives)
        )

    def test_large_offset_requires_stable_multi_window_evidence(self) -> None:
        frame_count = round(80 / 0.02)
        generator = np.random.default_rng(21)
        amplitudes = generator.uniform(0.01, 0.8, frame_count)
        master = np.repeat(amplitudes, round(SAMPLE_RATE * 0.02)).astype(np.float32)
        shift_frames = round(20 / 0.02)
        other_amplitudes = np.concatenate(
            (np.zeros(shift_frames), amplitudes[:-shift_frames])
        )
        other = np.repeat(other_amplitudes, round(SAMPLE_RATE * 0.02)).astype(
            np.float32
        )
        alternatives = rank_alignment_offsets(master, other, maximum_offset_seconds=30)
        best = alternatives[0]
        self.assertAlmostEqual(float(best["offset_seconds"]), 20.0, delta=0.03)
        self.assertTrue(best["large_offset"])
        self.assertTrue(best["accepted_for_automatic_use"])
        self.assertEqual(best["supported_windows"], 3)

    def test_sync_sanity_explains_reported_overlap_regression(self) -> None:
        cameras = (
            CameraSource("camera_01", Path("1.mp4"), duration_seconds=125.109002),
            CameraSource("camera_04", Path("4.mp4"), duration_seconds=97.106009),
            CameraSource("camera_03", Path("3.mp4"), duration_seconds=95.712993),
            CameraSource("camera_02", Path("2.mp4"), duration_seconds=43.05),
        )
        sanity = calculate_sync_sanity(
            cameras,
            master_camera="camera_01",
            timestamps={
                "camera_01": 3.19,
                "camera_04": 0.39,
                "camera_03": 49.0,
                "camera_02": 39.0,
            },
        )
        self.assertEqual(sanity["status"], "WARNING")
        self.assertAlmostEqual(
            float(sanity["common_usable_duration_seconds"]), 4.44, places=3
        )
        self.assertAlmostEqual(
            float(sanity["zero_offset_common_duration_seconds"]), 43.05, places=3
        )
        self.assertIn("camera_03", " ".join(sanity["warnings"]))

    def test_large_manual_offset_needs_explicit_risk_acknowledgement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "generated_sync.json"
            path.write_text(
                json.dumps(
                    {
                        "master_camera": "camera_01",
                        "clap_timestamps": {"camera_01": 3.19},
                        "camera_analyses": [
                            {"camera_id": "camera_01"},
                            {"camera_id": "camera_02"},
                        ],
                        "manual_confirmations": {
                            "camera_01": {"timestamp_seconds": 3.19}
                        },
                    }
                ),
                encoding="utf-8",
            )
            cameras = (
                CameraSource("camera_01", Path("1.mp4"), duration_seconds=125.109002),
                CameraSource("camera_02", Path("2.mp4"), duration_seconds=43.05),
            )
            with self.assertRaisesRegex(Exception, "risk acknowledgement"):
                confirm_sync_timestamp(
                    path,
                    camera_id="camera_02",
                    timestamp_seconds=39.0,
                    cameras=cameras,
                )
            accepted = confirm_sync_timestamp(
                path,
                camera_id="camera_02",
                timestamp_seconds=39.0,
                cameras=cameras,
                acknowledge_risk=True,
            )
            self.assertEqual(accepted["acceptance_status"], "verified")
            self.assertEqual(accepted["sync_sanity"]["status"], "WARNING")


if __name__ == "__main__":
    unittest.main()
