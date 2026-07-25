from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from src.errors import MediaProbeError, OutputValidationError
from src.media_probe import parse_ffprobe_output, probe_video, validate_output
from src.models import DurationPolicy, MediaMetadata


class MediaProbeTests(unittest.TestCase):
    @patch("src.media_probe.subprocess.run")
    def test_probe_forces_utf8_for_non_ascii_windows_paths(self, run: object) -> None:
        run.return_value.returncode = 0  # type: ignore[attr-defined]
        run.return_value.stdout = (  # type: ignore[attr-defined]
            '{"format":{"duration":"1"},'
            '"streams":[{"codec_type":"video","width":16,"height":16,'
            '"avg_frame_rate":"1/1"}]}'
        )
        run.return_value.stderr = ""  # type: ignore[attr-defined]
        metadata = probe_video(Path("视频.mp4"), ffprobe_executable="ffprobe")
        self.assertEqual(metadata.duration_seconds, 1)
        self.assertEqual(run.call_args.kwargs["encoding"], "utf-8")  # type: ignore[attr-defined]
        self.assertEqual(run.call_args.kwargs["errors"], "replace")  # type: ignore[attr-defined]

    def test_parses_video_and_audio_streams(self) -> None:
        metadata = parse_ffprobe_output(
            Path("sample.mp4"),
            {
                "format": {"duration": "72.040"},
                "streams": [
                    {
                        "codec_type": "video",
                        "codec_name": "h264",
                        "width": 1280,
                        "height": 720,
                        "avg_frame_rate": "30/1",
                    },
                    {"codec_type": "audio", "codec_name": "aac"},
                ],
            },
        )
        self.assertEqual(metadata.fps, 30)
        self.assertTrue(metadata.has_audio)

    def test_rejects_no_video(self) -> None:
        with self.assertRaises(MediaProbeError):
            parse_ffprobe_output(
                Path("audio.mp4"),
                {"format": {"duration": "10"}, "streams": [{"codec_type": "audio"}]},
            )

    def test_output_validation_checks_duration_and_audio(self) -> None:
        metadata = MediaMetadata(
            path=Path("draft.mp4"),
            duration_seconds=72.1,
            width=1280,
            height=720,
            fps=30,
            has_video=True,
            has_audio=True,
        )
        self.assertEqual(
            validate_output(
                metadata, DurationPolicy(60, 180, True), expected_duration_seconds=72
            ),
            (),
        )
        with self.assertRaises(OutputValidationError):
            validate_output(
                MediaMetadata(
                    path=Path("bad.mp4"),
                    duration_seconds=30,
                    width=1280,
                    height=720,
                    fps=30,
                    has_video=True,
                    has_audio=False,
                ),
                DurationPolicy(60, 180, True),
                expected_duration_seconds=72,
            )

    def test_duration_policy_can_exclude_presentation_screens(self) -> None:
        metadata = MediaMetadata(
            path=Path("draft.mp4"),
            duration_seconds=72,
            width=1280,
            height=720,
            fps=30,
            has_video=True,
            has_audio=True,
        )
        validate_output(
            metadata,
            DurationPolicy(64, 64, False),
            expected_duration_seconds=72,
            presentation_duration_seconds=8,
        )


if __name__ == "__main__":
    unittest.main()
