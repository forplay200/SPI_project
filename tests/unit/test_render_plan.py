from __future__ import annotations

import unittest
from pathlib import Path

from src.edl import parse_edl_data
from src.errors import RenderPlanError
from src.models import (
    CameraSource,
    DurationPolicy,
    OutputSpec,
    ProjectConfig,
    TextSpec,
)
from src.render_plan import build_render_plan, format_render_plan

from .test_edl import valid_edl_data


def config_with_offsets(*, early_offset: float = -1.0) -> ProjectConfig:
    return ProjectConfig(
        project="test",
        master_camera="a",
        renderer="moviepy",
        allow_ffmpeg_fallback=True,
        output=OutputSpec(),
        title=TextSpec("Title", 4),
        credits=TextSpec("Credits", 4),
        cameras=(
            CameraSource(
                "a",
                Path("a.mp4"),
                offset_seconds=0,
                duration_seconds=80,
                has_audio=True,
            ),
            CameraSource(
                "b",
                Path("b.mp4"),
                offset_seconds=early_offset,
                duration_seconds=80,
                has_audio=False,
            ),
        ),
        duration_policy=DurationPolicy(60, 180, True),
    )


class RenderPlanTests(unittest.TestCase):
    def test_maps_zero_and_negative_offsets_and_preserves_fields(self) -> None:
        edl = parse_edl_data(valid_edl_data())
        plan = build_render_plan(config_with_offsets(), edl)
        self.assertEqual(plan.instructions[0].source_start, 0)
        self.assertEqual(plan.instructions[1].source_start, 15)
        self.assertEqual(plan.instructions[1].reason, "Closer speech")
        self.assertIsNotNone(plan.instructions[1].overlay)
        self.assertEqual(plan.expected_duration_seconds, 72)
        self.assertIn("Camera switches: 3", format_render_plan(plan))

    def test_maps_positive_offset(self) -> None:
        plan = build_render_plan(
            config_with_offsets(early_offset=2.2), parse_edl_data(valid_edl_data())
        )
        self.assertEqual(plan.instructions[1].source_start, 18.2)

    def test_rejects_negative_source_boundary(self) -> None:
        data = valid_edl_data()
        data["timeline"][0]["camera"] = "b"  # type: ignore[index]
        with self.assertRaises(RenderPlanError) as raised:
            build_render_plan(
                config_with_offsets(early_offset=-1), parse_edl_data(data)
            )
        self.assertIn("negative source start", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
