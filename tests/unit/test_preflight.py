from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.preflight import resolve_executable


class ExecutableResolutionTests(unittest.TestCase):
    def test_finds_repository_local_tool_when_path_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "temp" / "ffmpeg-build" / "bin" / "ffprobe.exe"
            executable.parent.mkdir(parents=True)
            executable.touch()
            with (
                patch("src.preflight.shutil.which", return_value=None),
                patch("src.preflight.Path.cwd", return_value=root),
                patch("src.preflight.os.name", "nt"),
            ):
                resolved = resolve_executable("ffprobe")
            self.assertEqual(resolved, str(executable.resolve()))


if __name__ == "__main__":
    unittest.main()
