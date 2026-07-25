from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.edl import parse_edl_data
from src.errors import FFmpegRenderError
from src.ffmpeg_renderer import FFmpegRenderer, build_ffmpeg_command
from src.render_plan import build_render_plan

from .test_edl import valid_edl_data
from .test_render_plan import config_with_offsets


class FFmpegRendererTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_render_plan(
            config_with_offsets(early_offset=0), parse_edl_data(valid_edl_data())
        )

    def test_command_uses_filter_graph_and_mp4_output(self) -> None:
        command, graph = build_ffmpeg_command(
            self.plan, Path("draft.mp4"), ffmpeg_executable="ffmpeg"
        )
        self.assertEqual(command[0], "ffmpeg")
        self.assertIn("-filter_complex", command)
        self.assertEqual(command[-1], "draft.mp4")
        self.assertIn("concat=n=6:v=1:a=1", graph)
        self.assertIn("drawtext", graph)
        self.assertIn("fade=t=in", graph)

    @patch("src.ffmpeg_renderer.subprocess.run")
    def test_subprocess_is_shell_false_and_failure_is_visible(
        self, run: object
    ) -> None:
        run.return_value.returncode = 1  # type: ignore[attr-defined]
        run.return_value.stderr = "encoder error"  # type: ignore[attr-defined]
        run.return_value.stdout = ""  # type: ignore[attr-defined]
        with (
            tempfile.TemporaryDirectory() as directory,
            self.assertRaises(FFmpegRenderError),
        ):
            FFmpegRenderer(ffmpeg_executable="ffmpeg").render(
                self.plan, Path(directory) / "draft.mp4"
            )
        self.assertFalse(run.call_args.kwargs["shell"])  # type: ignore[attr-defined]
        self.assertIsInstance(run.call_args.args[0], list)  # type: ignore[attr-defined]


if __name__ == "__main__":
    unittest.main()
