from __future__ import annotations

import unittest
from pathlib import Path

from src.edl import parse_edl_data, validate_edl
from src.errors import EDLValidationError
from src.models import (
    CameraSource,
    DurationPolicy,
    OutputSpec,
    ProjectConfig,
    TextSpec,
)


def project_config() -> ProjectConfig:
    return ProjectConfig(
        project="test",
        master_camera="a",
        renderer="moviepy",
        allow_ffmpeg_fallback=True,
        output=OutputSpec(),
        title=TextSpec("Title", 4),
        credits=TextSpec("Credits", 4),
        cameras=(CameraSource("a", Path("a.mp4")), CameraSource("b", Path("b.mp4"))),
        duration_policy=DurationPolicy(60, 180, True),
    )


def valid_edl_data() -> dict[str, object]:
    return {
        "project": "test",
        "timeline": [
            {
                "id": "s1",
                "start": 0,
                "end": 16,
                "camera": "a",
                "reason": "Wide opening",
                "action": "fade_in",
            },
            {
                "id": "s2",
                "start": 16,
                "end": 32,
                "camera": "b",
                "reason": "Closer speech",
                "action": "cut",
                "overlay": {
                    "type": "lower_third",
                    "text": "Speech",
                    "start": 17,
                    "end": 21,
                    "position": "bottom",
                },
            },
            {
                "id": "s3",
                "start": 32,
                "end": 48,
                "camera": "a",
                "reason": "Group view",
                "action": "cut",
            },
            {
                "id": "s4",
                "start": 48,
                "end": 64,
                "camera": "b",
                "reason": "Closing detail",
                "action": "fade_out",
            },
        ],
    }


class EDLTests(unittest.TestCase):
    def test_valid_edl_has_three_switches(self) -> None:
        edl = parse_edl_data(valid_edl_data())
        validate_edl(edl, project_config())
        self.assertEqual(edl.switch_count, 3)

    def test_rejects_overlap_unknown_camera_and_too_few_switches(self) -> None:
        data = valid_edl_data()
        timeline = data["timeline"]
        timeline[1]["start"] = 15  # type: ignore[index]
        timeline[1]["camera"] = "missing"  # type: ignore[index]
        timeline[2]["camera"] = "b"  # type: ignore[index]
        timeline[3]["camera"] = "b"  # type: ignore[index]
        edl = parse_edl_data(data)
        with self.assertRaises(EDLValidationError) as raised:
            validate_edl(edl, project_config())
        message = str(raised.exception)
        self.assertIn("overlap", message)
        self.assertIn("unknown camera", message)
        self.assertIn("three camera switches", message)

    def test_rejects_empty_reason_and_unsupported_action(self) -> None:
        data = valid_edl_data()
        data["timeline"][0]["reason"] = ""  # type: ignore[index]
        data["timeline"][0]["action"] = "crossfade"  # type: ignore[index]
        with self.assertRaises(EDLValidationError) as raised:
            parse_edl_data(data)
        self.assertIn("reason", str(raised.exception))
        self.assertIn("action", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
