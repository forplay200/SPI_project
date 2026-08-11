from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.errors import ConfigurationError
from src.validate_inputs import load_project_config


def valid_config() -> dict[str, object]:
    return {
        "project": "test-project",
        "master_camera": "cam-a",
        "renderer": "moviepy",
        "allow_ffmpeg_fallback": True,
        "output": {
            "width": 1280,
            "height": 720,
            "fps": 30,
            "video_codec": "libx264",
            "audio_codec": "aac",
        },
        "duration_policy": {
            "min_seconds": 60,
            "max_seconds": 180,
            "includes_title_and_credits": True,
        },
        "title": {"text": "Title", "duration": 4},
        "credits": {"text": "Credits", "duration": 4},
        "cameras": [
            {"id": "cam-a", "path": "input/a.mp4"},
            {"id": "cam-b", "path": "input/b.mp4"},
        ],
    }


class ProjectConfigTests(unittest.TestCase):
    def write_config(self, root: Path, data: dict[str, object]) -> Path:
        config_dir = root / "config"
        input_dir = root / "input"
        config_dir.mkdir()
        input_dir.mkdir()
        (input_dir / "a.mp4").touch()
        (input_dir / "b.mp4").touch()
        path = config_dir / "project.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_accepts_two_local_camera_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_config(Path(directory), valid_config())
            config = load_project_config(path)
            self.assertEqual(len(config.cameras), 2)
            self.assertEqual(config.master_camera, "cam-a")

    def test_rejects_duplicate_camera_ids_and_unknown_master(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = valid_config()
            data["master_camera"] = "missing"
            data["cameras"][1]["id"] = "cam-a"  # type: ignore[index]
            path = self.write_config(Path(directory), data)
            with self.assertRaises(ConfigurationError) as raised:
                load_project_config(path)
            self.assertIn("duplicates", str(raised.exception))
            self.assertIn("not present", str(raised.exception))

    def test_rejects_output_as_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = valid_config()
            data["cameras"][0]["path"] = "output/draft/a.mp4"  # type: ignore[index]
            path = self.write_config(Path(directory), data)
            with self.assertRaises(ConfigurationError) as raised:
                load_project_config(path, require_camera_files=False)
            self.assertIn("cannot point inside", str(raised.exception))

    def test_rejects_non_finite_numeric_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data = valid_config()
            data["duration_policy"]["min_seconds"] = float("nan")  # type: ignore[index]
            path = self.write_config(Path(directory), data)
            with self.assertRaises(ConfigurationError) as raised:
                load_project_config(path)
            self.assertIn("min_seconds must be finite", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
