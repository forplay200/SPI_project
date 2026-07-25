from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from src.edl_generator import generate_edl, maximum_honest_output_duration
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

    def test_insufficient_duration_fails_with_maximum_honest_duration(self) -> None:
        config = generator_config(source_duration=26)
        self.assertEqual(maximum_honest_output_duration(config), 34)
        with self.assertRaises(PreparationError) as raised:
            generate_edl(config, requested_duration_seconds=90)
        self.assertIn("maximum honest", str(raised.exception))
        self.assertIn("34.000", str(raised.exception))

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
