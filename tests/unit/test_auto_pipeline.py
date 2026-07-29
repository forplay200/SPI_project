from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from src.auto_pipeline import DEFAULT_CREDITS_TEXT, prepare_automatic, run_automatic
from src.errors import PreparationError
from src.main import build_parser
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


def grouping_audio(offset: float = 0.0) -> np.ndarray:
    samples = np.zeros(SAMPLE_RATE * 18, dtype=np.float32)
    for timestamp in (1.0, 6.0, 11.0, 16.0):
        start = round((timestamp + offset) * SAMPLE_RATE)
        samples[start : start + round(0.03 * SAMPLE_RATE)] = 1
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
        credits: str | None = None,
        credits_duration: float | None = None,
    ):
        first, _ = self.create_inputs(root)

        def decoded(path: Path, **_: object) -> np.ndarray:
            return grouping_audio(0.0 if path == first else 0.2)

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
                    **{
                        **ffprobe_payload.__dict__,
                        "path": path,
                        "width": 1920 if path == first else 1280,
                    }
                ),
            ),
            patch("src.sync_assistant.decode_audio_window", side_effect=decoded),
            patch("src.camera_grouping.decode_audio_window", side_effect=decoded),
            patch("src.auto_pipeline.prepare_pipeline"),
        ):
            options: dict[str, object] = {}
            if credits is not None:
                options["credits"] = credits
            if credits_duration is not None:
                options["credits_duration"] = credits_duration
            return prepare_automatic(
                project_root=root,
                input_path=root / "input",
                requested_duration_seconds=requested_duration,
                title="Synthetic Ceremony",
                allow_smoke=allow_smoke,
                **options,
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
            self.assertEqual(config.credits.text, DEFAULT_CREDITS_TEXT)
            self.assertEqual(config.credits.duration, 4.0)
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
                AutomationOutcome.INSUFFICIENT_RENDERABLE_DURATION,
            )
            self.assertFalse(insufficient.render_permitted)
            summary = json.loads(insufficient.summary_path.read_text())
            self.assertIn("common_overlap_duration", summary)
            self.assertIn("total_event_coverage", summary)
            self.assertIn("maximum_renderable_duration", summary)
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

    def test_generated_credits_use_professional_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.prepare_with_mock_media(
                Path(directory),
                source_duration=100,
                requested_duration=18,
                allow_smoke=True,
            )
            config = load_project_config(result.project_path)
            self.assertEqual(config.credits.text, DEFAULT_CREDITS_TEXT)
            self.assertEqual(config.credits.duration, 1.0)
            self.assertNotIn("human review required", config.credits.text.casefold())

    def test_custom_credits_and_duration_are_written_to_generated_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.prepare_with_mock_media(
                Path(directory),
                source_duration=100,
                requested_duration=20,
                allow_smoke=True,
                credits="  Edited by the Project Team | BTIS3053  ",
                credits_duration=4,
            )
            config = load_project_config(result.project_path)
            self.assertEqual(
                config.credits.text, "Edited by the Project Team | BTIS3053"
            )
            self.assertEqual(config.credits.duration, 4.0)

    def test_credit_options_are_validated_before_media_processing(self) -> None:
        for invalid_duration in (0.0, -1.0, float("nan"), float("inf")):
            with (
                self.subTest(credits_duration=invalid_duration),
                self.assertRaisesRegex(
                    PreparationError, "credits-duration must be a finite number"
                ),
            ):
                prepare_automatic(
                    project_root=Path("."),
                    input_path=Path("input"),
                    requested_duration_seconds=90,
                    title="Synthetic",
                    credits_duration=invalid_duration,
                )
        with self.assertRaisesRegex(PreparationError, "credits must be a non-empty"):
            prepare_automatic(
                project_root=Path("."),
                input_path=Path("input"),
                requested_duration_seconds=90,
                title="Synthetic",
                credits="   ",
            )

    def test_prepare_and_auto_cli_accept_credit_options(self) -> None:
        parser = build_parser()
        for command in ("prepare", "auto"):
            args = parser.parse_args(
                [
                    command,
                    "--credits",
                    "Edited by Team | BTIS3053",
                    "--credits-duration",
                    "4",
                ]
            )
            self.assertEqual(args.credits, "Edited by Team | BTIS3053")
            self.assertEqual(args.credits_duration, 4.0)
        defaults = parser.parse_args(["auto"])
        self.assertEqual(defaults.credits, DEFAULT_CREDITS_TEXT)
        self.assertIsNone(defaults.credits_duration)

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
                        **{
                            **metadata.__dict__,
                            "path": path,
                            "width": 1920 if path == first else 1280,
                        }
                    ),
                ),
                patch(
                    "src.sync_assistant.decode_audio_window",
                    return_value=grouping_audio(),
                ),
                patch(
                    "src.camera_grouping.decode_audio_window",
                    return_value=grouping_audio(),
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

    def test_explicit_camera_selection_bypasses_only_grouping(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first, second = self.create_inputs(root)
            metadata = MediaMetadata(
                path=first,
                duration_seconds=20,
                width=1280,
                height=720,
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
                        **{**metadata.__dict__, "path": path}
                    ),
                ),
                patch(
                    "src.sync_assistant.decode_audio_window",
                    return_value=grouping_audio(),
                ),
                patch("src.auto_pipeline.prepare_pipeline"),
            ):
                result = prepare_automatic(
                    project_root=root,
                    input_path=root / "input",
                    requested_duration_seconds=18,
                    title="Explicit",
                    allow_smoke=True,
                    camera_files=(Path(first.name), Path(second.name)),
                )
            self.assertTrue(result.render_permitted)
            self.assertEqual(result.camera_group_state, "CAMERA_GROUP_CONFIRMED")
            self.assertEqual(result.analysed_pair_count, 0)
            self.assertEqual(len(result.selected_camera_paths), 2)

    def test_low_confidence_group_requires_explicit_human_verification_override(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first, _ = self.create_inputs(root)
            metadata = MediaMetadata(
                path=first,
                duration_seconds=100,
                width=1280,
                height=720,
                fps=30,
                has_video=True,
                has_audio=True,
                video_codec="h264",
                audio_codec="aac",
            )
            generator = np.random.default_rng(91)
            grouping_samples = [
                generator.normal(0, 0.1, SAMPLE_RATE * 18).astype(np.float32),
                generator.normal(0, 0.1, SAMPLE_RATE * 18).astype(np.float32),
            ]
            prepared = unittest.mock.MagicMock(spec=PreparedPipeline)
            draft = root / "output" / "draft" / "override-smoke_draft.mp4"
            render_result = RenderResult(draft, "moviepy", "start", "end", 18.0)
            with (
                patch(
                    "src.video_discovery.probe_video",
                    side_effect=lambda path, **_: MediaMetadata(
                        **{**metadata.__dict__, "path": path}
                    ),
                ),
                patch(
                    "src.camera_grouping.decode_audio_window",
                    side_effect=grouping_samples,
                ),
                patch(
                    "src.sync_assistant.decode_audio_window",
                    return_value=grouping_audio(),
                ),
                patch("src.auto_pipeline.prepare_pipeline", return_value=prepared),
                patch(
                    "src.auto_pipeline.render_draft",
                    return_value=(render_result, metadata, root / "render.json"),
                ),
            ):
                result, _, rendered = run_automatic(
                    project_root=root,
                    input_path=root / "input",
                    requested_duration_seconds=18,
                    title="Human confirmed event",
                    allow_smoke=True,
                    continue_low_confidence=True,
                )
            self.assertEqual(
                result.camera_group_state,
                "CAMERA_GROUP_LOW_CONFIDENCE",
            )
            self.assertEqual(len(result.selected_camera_paths), 2)
            self.assertIsNotNone(rendered)
            self.assertEqual(
                result.outcome,
                AutomationOutcome.DRAFT_RENDERED_WITH_UNVERIFIED_SYNC,
            )
            self.assertTrue(any("explicitly" in warning for warning in result.warnings))


if __name__ == "__main__":
    unittest.main()
