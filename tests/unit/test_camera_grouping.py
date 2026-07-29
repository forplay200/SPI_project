from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from src.camera_grouping import (
    group_camera_sources,
    normalise_filename_timestamp,
    score_camera_pair,
)
from src.models import (
    CameraGroupingState,
    DiscoveredVideo,
    PairwiseCameraScore,
)
from src.sync_assistant import SAMPLE_RATE


def event_audio(offset: float = 0.0, *, duration: float = 18.0) -> np.ndarray:
    samples = np.zeros(round(duration * SAMPLE_RATE), dtype=np.float32)
    for timestamp, strength in ((1.0, 1.0), (6.0, 0.8), (11.0, 0.9), (16.0, 0.7)):
        start = round((timestamp + offset) * SAMPLE_RATE)
        samples[start : start + round(0.04 * SAMPLE_RATE)] = strength
    return samples


def discovered(
    camera_id: str,
    name: str,
    *,
    duration: float = 20.0,
    width: int = 1280,
    creation_time: str | None = None,
) -> DiscoveredVideo:
    return DiscoveredVideo(
        camera_id=camera_id,
        path=Path(name),
        relative_path=f"input/{name}",
        duration_seconds=duration,
        width=width,
        height=720,
        display_rotation=0,
        fps=30,
        video_codec="h264",
        has_audio=True,
        audio_codec="aac",
        classification="likely_source",
        usable=True,
        creation_time=creation_time,
    )


class FilenameTimestampTests(unittest.TestCase):
    def test_normalises_compact_separated_and_unicode_names(self) -> None:
        expected = (2026, 6, 19, 15, 15, 29)
        for name in (
            "VID_20260619_151529.mp4",
            "VID20260619151529.mp4",
            "video-20260619-151529.mp4",
            "视频-20260619-151529-f92c617d.mov",
        ):
            parsed = normalise_filename_timestamp(name)
            self.assertIsNotNone(parsed)
            self.assertEqual(
                (
                    parsed.year,
                    parsed.month,
                    parsed.day,
                    parsed.hour,
                    parsed.minute,
                    parsed.second,
                ),
                expected,
            )

    def test_filename_without_timestamp_returns_none(self) -> None:
        self.assertIsNone(normalise_filename_timestamp("Demo.mp4"))


class PairwiseScoringTests(unittest.TestCase):
    def test_positive_and_negative_offsets_are_recovered(self) -> None:
        first = discovered("camera_01", "one.mp4", width=1280)
        second = discovered("camera_02", "two.mp4", width=1920)
        positive = score_camera_pair(
            first,
            second,
            first_samples=event_audio(),
            second_samples=event_audio(0.3),
            minimum_common_duration_seconds=8,
        )
        negative = score_camera_pair(
            first,
            second,
            first_samples=event_audio(),
            second_samples=event_audio(-0.25),
            minimum_common_duration_seconds=8,
        )
        self.assertAlmostEqual(positive.estimated_offset_seconds or 0, 0.3, delta=0.03)
        self.assertAlmostEqual(
            negative.estimated_offset_seconds or 0, -0.26, delta=0.03
        )
        self.assertTrue(positive.accepted)
        self.assertTrue(negative.accepted)

    def test_unrelated_audio_and_low_confidence_are_rejected(self) -> None:
        first = discovered("camera_01", "one.mp4")
        second = discovered("camera_02", "two.mp4", width=1920)
        generator = np.random.default_rng(7)
        unrelated = score_camera_pair(
            first,
            second,
            first_samples=generator.normal(0, 0.1, SAMPLE_RATE * 18).astype(np.float32),
            second_samples=generator.normal(0, 0.1, SAMPLE_RATE * 18).astype(
                np.float32
            ),
            minimum_common_duration_seconds=8,
        )
        no_audio = score_camera_pair(
            first,
            second,
            first_samples=None,
            second_samples=None,
            minimum_common_duration_seconds=8,
        )
        self.assertFalse(unrelated.accepted)
        self.assertLess(unrelated.audio_correlation, 0.45)
        self.assertFalse(no_audio.accepted)

    def test_identical_stream_is_rejected_as_derived_duplicate(self) -> None:
        first = discovered("camera_01", "source.mp4")
        second = discovered("camera_02", "copy.mp4")
        samples = event_audio()
        score = score_camera_pair(
            first,
            second,
            first_samples=samples,
            second_samples=samples.copy(),
            minimum_common_duration_seconds=8,
        )
        self.assertGreaterEqual(score.derived_duplicate_likelihood, 0.7)
        self.assertFalse(score.accepted)


class CameraGroupSelectionTests(unittest.TestCase):
    def test_three_compatible_cameras_selected_and_unrelated_rejected(self) -> None:
        videos = (
            discovered("camera_01", "a.mp4", width=640),
            discovered("camera_02", "b.mp4", width=1280),
            discovered("camera_03", "c.mp4", width=1920),
            discovered("camera_04", "unrelated.mp4", width=3840),
        )
        unrelated = (
            np.random.default_rng(5).normal(0, 0.1, SAMPLE_RATE * 18).astype(np.float32)
        )
        audio = {
            "a.mp4": event_audio(),
            "b.mp4": event_audio(0.2),
            "c.mp4": event_audio(-0.2),
            "unrelated.mp4": unrelated,
        }
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "camera_grouping.json"
            with patch(
                "src.camera_grouping.decode_audio_window",
                side_effect=lambda path, **_: audio[path.name],
            ):
                result = group_camera_sources(
                    videos,
                    input_path=Path("."),
                    minimum_common_duration_seconds=8,
                    report_path=report_path,
                )
            self.assertTrue(report_path.is_file())
        self.assertEqual(
            [video.camera_id for video in result.selected_videos],
            ["camera_01", "camera_02", "camera_03"],
        )
        self.assertNotIn(
            "camera_04", [video.camera_id for video in result.selected_videos]
        )
        self.assertEqual(result.analysed_pair_count, 6)

    def test_deterministic_tie_breaking_uses_stable_camera_ids(self) -> None:
        videos = tuple(
            discovered(f"camera_{index:02d}", f"{index}.mp4", width=600 + index)
            for index in range(1, 5)
        )

        def fake_score(first: DiscoveredVideo, second: DiscoveredVideo, **_: object):
            accepted = {first.camera_id, second.camera_id} in (
                {"camera_01", "camera_02"},
                {"camera_03", "camera_04"},
            )
            return PairwiseCameraScore(
                first.camera_id or "",
                second.camera_id or "",
                first.relative_path,
                second.relative_path,
                None,
                None,
                1,
                20,
                True,
                0.8 if accepted else 0.1,
                0,
                1,
                2,
                0.8,
                1,
                0,
                0.8 if accepted else 0.1,
                "high" if accepted else "low",
                accepted,
                "accepted" if accepted else "rejected",
            )

        with (
            patch(
                "src.camera_grouping.decode_audio_window", return_value=event_audio()
            ),
            patch("src.camera_grouping.score_camera_pair", side_effect=fake_score),
        ):
            first = group_camera_sources(videos, input_path=Path("."))
            second = group_camera_sources(videos, input_path=Path("."))
        self.assertEqual(first.selected_videos, second.selected_videos)
        self.assertEqual(
            [video.camera_id for video in first.selected_videos],
            ["camera_01", "camera_02"],
        )

    def test_no_reliable_group_reports_highest_rejected_pair(self) -> None:
        videos = (
            discovered("camera_01", "a.mp4"),
            discovered("camera_02", "b.mp4", width=1920),
        )
        generator = np.random.default_rng(11)
        with patch(
            "src.camera_grouping.decode_audio_window",
            side_effect=[
                generator.normal(0, 0.1, SAMPLE_RATE * 18).astype(np.float32),
                generator.normal(0, 0.1, SAMPLE_RATE * 18).astype(np.float32),
            ],
        ):
            result = group_camera_sources(videos, input_path=Path("."))
        self.assertEqual(result.state, CameraGroupingState.CAMERA_GROUP_LOW_CONFIDENCE)
        self.assertEqual(result.selected_videos, ())
        self.assertEqual(
            [video.camera_id for video in result.suggested_videos],
            ["camera_01", "camera_02"],
        )
        self.assertIn("suggested for human verification", result.reason)
        self.assertTrue(result.pair_scores[0].suggested)


if __name__ == "__main__":
    unittest.main()
