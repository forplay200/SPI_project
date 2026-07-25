from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from src.auto_pipeline import prepare_automatic, run_automatic
from src.models import (
    AutomationOutcome,
    MediaMetadata,
    RenderResult,
)
from src.pipeline import PreparedPipeline
from src.sync_assistant import SAMPLE_RATE
from src.validate_inputs import load_project_config


def audio_at(timestamp: float) -> np.ndarray:
    samples = np.zeros(SAMPLE_RATE * 3, dtype=np.float32)
    start = round(timestamp * SAMPLE_RATE)
    samples[start : start + round(0.02 * SAMPLE_RATE)] = 1
    return samples


class AutoPipelineTests(unittest.TestCase):
    def create_inputs(self, root: Path) -> tuple[Path, Path]:
        input_path = root / "input"
        input_path.mkdir()
        first = input_path / "cam_a_20260726_120000.mp4"
        second = input_path / "cam_b_20260726_120000.mp4"
        first.touch()
        second.touch()
        return first, second

    def prepare_with_mock_media(
        self,
        root: Path,
        *,
        source_duration: float,
        requested_duration: float,
        allow_smoke: bool = False,
    ):
        first, _ = self.create_inputs(root)

        def decoded(path: Path, **_: object) -> np.ndarray:
            return audio_at(1.0 if path == first else 1.2)

        ffprobe_payload = MediaMetadata(
            path=first,
            duration_seconds=source_duration,
            width=1920,
            height=1080,
            fps=30,
            has_video=True,
            has_audio=True,
            video_codec="h264",
            audio_codec="aac",
        )
        with (
            patch(
                "src.video_discovery.probe_video",
                side_effect=lambda path, **_: MediaMetadata(
                    **{**ffprobe_payload.__dict__, "path": path}
                ),
            ),
            patch("src.sync_assistant.decode_audio_window", side_effect=decoded),
            patch("src.auto_pipeline.prepare_pipeline"),
        ):
            return prepare_automatic(
                project_root=root,
                input_path=root / "input",
                requested_duration_seconds=requested_duration,
                title="Synthetic Ceremony",
                allow_smoke=allow_smoke,
            )

    def test_prepare_generates_valid_project_sync_edl_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self.prepare_with_mock_media(
                root, source_duration=100, requested_duration=90
            )
            self.assertEqual(result.outcome, AutomationOutcome.NEEDS_SYNC_CONFIRMATION)
            self.assertTrue(result.render_permitted)
            self.assertTrue(result.project_path and result.project_path.is_file())
            self.assertTrue(result.sync_path and result.sync_path.is_file())
            self.assertTrue(result.edl_path and result.edl_path.is_file())
            config = load_project_config(result.project_path)
            self.assertEqual(len(config.cameras), 2)
            edl = json.loads(result.edl_path.read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(edl["timeline"]), 4)
            self.assertTrue(
                json.loads(result.summary_path.read_text())["final_approval_performed"]
                is False
            )

    def test_insufficient_duration_and_explicit_smoke_are_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            insufficient = self.prepare_with_mock_media(
                root, source_duration=20, requested_duration=90
            )
            self.assertEqual(
                insufficient.outcome,
                AutomationOutcome.INSUFFICIENT_COMMON_DURATION,
            )
            self.assertFalse(insufficient.render_permitted)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            smoke = self.prepare_with_mock_media(
                root,
                source_duration=20,
                requested_duration=18,
                allow_smoke=True,
            )
            self.assertEqual(smoke.outcome, AutomationOutcome.READY_FOR_SMOKE_ONLY)
            self.assertTrue(smoke.smoke)
            self.assertIn("smoke", load_project_config(smoke.project_path).project)

    def test_auto_renders_draft_but_never_approves(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first, _ = self.create_inputs(root)
            metadata = MediaMetadata(
                path=first,
                duration_seconds=100,
                width=1920,
                height=1080,
                fps=30,
                has_video=True,
                has_audio=True,
                video_codec="h264",
                audio_codec="aac",
            )
            draft = root / "output" / "draft" / "synthetic-unverified-sync_draft.mp4"
            render_result = RenderResult(draft, "moviepy", "start", "end", 1.0)
            prepared = unittest.mock.MagicMock(spec=PreparedPipeline)
            with (
                patch(
                    "src.video_discovery.probe_video",
                    side_effect=lambda path, **_: MediaMetadata(
                        **{**metadata.__dict__, "path": path}
                    ),
                ),
                patch(
                    "src.sync_assistant.decode_audio_window",
                    return_value=audio_at(1.0),
                ),
                patch("src.auto_pipeline.prepare_pipeline", return_value=prepared),
                patch(
                    "src.auto_pipeline.render_draft",
                    return_value=(render_result, metadata, root / "render.json"),
                ),
                patch("src.review.promote_approved_draft") as approve,
            ):
                result, _, rendered = run_automatic(
                    project_root=root,
                    input_path=root / "input",
                    requested_duration_seconds=90,
                    title="Synthetic",
                )
            self.assertEqual(
                result.outcome,
                AutomationOutcome.DRAFT_RENDERED_WITH_UNVERIFIED_SYNC,
            )
            self.assertIsNotNone(rendered)
            approve.assert_not_called()


if __name__ == "__main__":
    unittest.main()
