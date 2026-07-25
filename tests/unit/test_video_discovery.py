from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.errors import MediaProbeError
from src.models import MediaMetadata
from src.video_discovery import discover_videos, select_related_camera_group


def metadata(path: Path, *, audio: bool = True) -> MediaMetadata:
    return MediaMetadata(
        path=path,
        duration_seconds=70,
        width=1920,
        height=1080,
        fps=30,
        has_video=True,
        has_audio=audio,
        video_codec="h264",
        audio_codec="aac" if audio else None,
        display_rotation=-90,
    )


class VideoDiscoveryTests(unittest.TestCase):
    def test_recursive_filtering_exclusions_and_stable_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "input"
            (input_path / "nested").mkdir(parents=True)
            (input_path / "output").mkdir()
            for relative in (
                "cam_20260726_120000_b.MOV",
                "nested/cam_20260726_120000_a.mp4",
                "notes.txt",
                "project_draft.mp4",
                "output/hidden.mkv",
            ):
                path = input_path / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            with patch(
                "src.video_discovery.probe_video",
                side_effect=lambda path, **_: metadata(path),
            ):
                first = discover_videos(input_path, project_root=root)
                second = discover_videos(input_path, project_root=root)
            self.assertEqual(
                [item.camera_id for item in first.usable_videos],
                ["camera_01", "camera_02"],
            )
            self.assertEqual(
                [item.relative_path for item in first.usable_videos],
                [item.relative_path for item in second.usable_videos],
            )
            self.assertFalse(
                any("output/hidden" in item.relative_path for item in first.videos)
            )
            derived = next(
                item for item in first.videos if "project_draft" in item.relative_path
            )
            self.assertEqual(derived.classification, "likely_derived_output")
            self.assertFalse(derived.usable)
            self.assertEqual(len(select_related_camera_group(first.videos)), 2)

    def test_invalid_media_is_reported_without_inventing_camera_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "input"
            input_path.mkdir()
            bad = input_path / "broken.mp4"
            bad.touch()
            with patch(
                "src.video_discovery.probe_video",
                side_effect=MediaProbeError("zero duration"),
            ):
                report = discover_videos(input_path, project_root=root)
            self.assertEqual(len(report.usable_videos), 0)
            self.assertIsNone(report.videos[0].camera_id)
            self.assertIn("zero duration", report.videos[0].warnings[0])

    def test_include_derived_probes_explicitly_included_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "input"
            input_path.mkdir()
            rendered = input_path / "rendered_take.mkv"
            rendered.touch()
            with patch(
                "src.video_discovery.probe_video", return_value=metadata(rendered)
            ):
                report = discover_videos(
                    input_path, project_root=root, include_derived=True
                )
            self.assertEqual(report.usable_videos[0].camera_id, "camera_01")


if __name__ == "__main__":
    unittest.main()
