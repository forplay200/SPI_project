from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from src.edl_generator import calculate_duration_metrics, generate_edl
from src.errors import PreparationError
from src.models import (
    CameraSource,
    DurationPolicy,
    OutputSpec,
    ProjectConfig,
    TextSpec,
)


def generator_config(
    *,
    source_duration: float = 100,
    policy: DurationPolicy | None = None,
) -> ProjectConfig:
    return ProjectConfig(
        project="generated-test",
        master_camera="camera_01",
        renderer="moviepy",
        allow_ffmpeg_fallback=True,
        output=OutputSpec(),
        title=TextSpec("Title", 4),
        credits=TextSpec("Credits", 4),
        cameras=(
            CameraSource(
                "camera_01",
                Path("a.mp4"),
                duration_seconds=source_duration,
                has_audio=True,
            ),
            CameraSource(
                "camera_02",
                Path("b.mp4"),
                offset_seconds=0.3,
                duration_seconds=source_duration + 0.3,
                has_audio=True,
            ),
        ),
        duration_policy=policy or DurationPolicy(60, 180, True),
    )


class EDLGeneratorTests(unittest.TestCase):
    def test_deterministic_two_camera_edl_meets_all_contracts(self) -> None:
        config = generator_config()
        first, metadata = generate_edl(config, requested_duration_seconds=90)
        second, _ = generate_edl(config, requested_duration_seconds=90)
        self.assertEqual(first, second)
        self.assertGreaterEqual(first.switch_count, 3)
        self.assertEqual(
            {item.camera for item in first.timeline}, {"camera_01", "camera_02"}
        )
        self.assertEqual(first.timeline[0].action, "fade_in")
        self.assertEqual(first.timeline[-1].action, "fade_to_black")
        self.assertTrue(any(item.overlay for item in first.timeline))
        self.assertTrue(all(item.reason for item in first.timeline))
        self.assertTrue(
            all(
                current.start == previous.end
                for previous, current in zip(first.timeline, first.timeline[1:])
            )
        )
        self.assertLessEqual(first.timeline[-1].end + 0.3, 100.3)
        self.assertFalse(metadata["machine_learning_used"])

    def test_insufficient_duration_fails_with_maximum_renderable_duration(self) -> None:
        config = generator_config(source_duration=40)
        metrics = calculate_duration_metrics(config)
        self.assertEqual(metrics.maximum_renderable_duration, 48)
        with self.assertRaises(PreparationError) as raised:
            generate_edl(config, requested_duration_seconds=90)
        self.assertIn("maximum renderable", str(raised.exception))
        self.assertIn("48.000", str(raised.exception))

    def test_coverage_union_is_distinct_from_common_overlap(self) -> None:
        config = replace(
            generator_config(source_duration=40),
            cameras=(
                CameraSource("camera_01", Path("a.mp4"), duration_seconds=40),
                CameraSource(
                    "camera_02",
                    Path("b.mp4"),
                    offset_seconds=10,
                    duration_seconds=40,
                ),
            ),
        )
        metrics = calculate_duration_metrics(config)
        self.assertEqual(metrics.common_overlap_duration, 30)
        self.assertEqual(metrics.total_event_coverage, 50)

    def test_disconnected_union_is_not_treated_as_renderable_continuity(self) -> None:
        config = replace(
            generator_config(),
            cameras=(
                CameraSource("camera_01", Path("a.mp4"), duration_seconds=50),
                CameraSource("camera_02", Path("b.mp4"), duration_seconds=50),
                CameraSource(
                    "camera_03",
                    Path("c.mp4"),
                    offset_seconds=-100,
                    duration_seconds=50,
                ),
                CameraSource(
                    "camera_04",
                    Path("d.mp4"),
                    offset_seconds=-100,
                    duration_seconds=50,
                ),
            ),
        )
        metrics = calculate_duration_metrics(config)
        self.assertEqual(metrics.common_overlap_duration, 0)
        self.assertEqual(metrics.total_event_coverage, 100)
        self.assertEqual(metrics.maximum_renderable_duration, 58)
        with self.assertRaisesRegex(PreparationError, "maximum renderable"):
            generate_edl(config, requested_duration_seconds=90)

    def test_120_second_regression_uses_per_segment_camera_coverage(self) -> None:
        config = replace(
            generator_config(),
            cameras=(
                CameraSource("camera_01", Path("1.mp4"), duration_seconds=125.109002),
                CameraSource(
                    "camera_04",
                    Path("4.mp4"),
                    offset_seconds=-2.8,
                    duration_seconds=97.106009,
                ),
                CameraSource(
                    "camera_03",
                    Path("3.mp4"),
                    offset_seconds=45.81,
                    duration_seconds=95.712993,
                ),
                CameraSource(
                    "camera_02",
                    Path("2.mp4"),
                    offset_seconds=35.81,
                    duration_seconds=43.05,
                ),
            ),
        )
        metrics = calculate_duration_metrics(config)
        self.assertAlmostEqual(metrics.common_overlap_duration, 4.44, places=3)
        self.assertAlmostEqual(metrics.total_event_coverage, 170.919002, places=3)
        self.assertGreaterEqual(metrics.maximum_renderable_duration, 120)

        edl, metadata = generate_edl(config, requested_duration_seconds=120)

        self.assertEqual(edl.main_duration_seconds, 112)
        self.assertGreaterEqual(edl.switch_count, 3)
        self.assertGreater(edl.main_duration_seconds, metrics.common_overlap_duration)
        self.assertEqual(metadata["common_overlap_duration"], 4.44)
        self.assertEqual(
            metadata["maximum_renderable_duration"],
            metrics.maximum_renderable_duration,
        )

    def test_smoke_mode_is_explicit_and_still_has_three_switches(self) -> None:
        config = replace(
            generator_config(source_duration=20),
            project="generated-test-smoke",
            title=TextSpec("Smoke", 1),
            credits=TextSpec("Smoke credits", 1),
            duration_policy=DurationPolicy(17.5, 18.5, True),
        )
        edl, metadata = generate_edl(
            config, requested_duration_seconds=18, allow_smoke=True
        )
        self.assertEqual(edl.switch_count, 3)
        self.assertEqual(edl.main_duration_seconds, 16)
        self.assertTrue(metadata["smoke"])

    def test_non_smoke_rejects_out_of_policy_request(self) -> None:
        with self.assertRaises(PreparationError):
            generate_edl(generator_config(), requested_duration_seconds=18)


if __name__ == "__main__":
    unittest.main()
