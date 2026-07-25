from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from src.edl import parse_edl_data
from src.errors import MoviePyRenderError
from src.models import RenderResult
from src.render_plan import build_render_plan
from src.renderer import render_with_selected_backend

from .test_edl import valid_edl_data
from .test_render_plan import config_with_offsets


class RendererAdapterTests(unittest.TestCase):
    def test_moviepy_failure_activates_visible_ffmpeg_fallback(self) -> None:
        plan = build_render_plan(
            config_with_offsets(early_offset=0), parse_edl_data(valid_edl_data())
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "draft.mp4"
            fallback_result = RenderResult(
                output_path=output,
                backend="ffmpeg",
                started_at="start",
                completed_at="end",
                duration_seconds=1,
            )
            with (
                patch(
                    "src.moviepy_renderer.MoviePyRenderer.render",
                    side_effect=MoviePyRenderError("deliberate primary failure"),
                ),
                patch(
                    "src.ffmpeg_renderer.FFmpegRenderer.render",
                    return_value=fallback_result,
                ),
            ):
                result = render_with_selected_backend(
                    plan, output, ffmpeg_executable="ffmpeg"
                )
        self.assertEqual(result.backend, "ffmpeg")
        self.assertIn("deliberate primary failure", result.fallback_reason or "")
        self.assertTrue(any("fallback activated" in item for item in result.warnings))

    def test_disabled_fallback_preserves_moviepy_error(self) -> None:
        config = replace(
            config_with_offsets(early_offset=0), allow_ffmpeg_fallback=False
        )
        plan = build_render_plan(config, parse_edl_data(valid_edl_data()))
        with (
            patch(
                "src.moviepy_renderer.MoviePyRenderer.render",
                side_effect=MoviePyRenderError("primary failure"),
            ),
            self.assertRaises(MoviePyRenderError),
        ):
            render_with_selected_backend(plan, Path("draft.mp4"))


if __name__ == "__main__":
    unittest.main()
