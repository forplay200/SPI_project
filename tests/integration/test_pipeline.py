from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.auto_pipeline import run_automatic
from src.errors import MoviePyRenderError
from src.models import AutomationOutcome
from src.pipeline import prepare_pipeline, render_draft
from src.review import REVIEW_CHECKLIST_ITEMS, promote_approved_draft, record_review

RUN_MEDIA_TESTS = os.environ.get("PIPELINE_RUN_MEDIA_TESTS") == "1"
RUN_LONG_MEDIA_TESTS = os.environ.get("PIPELINE_RUN_LONG_MEDIA_TESTS") == "1"
FFMPEG = os.environ.get("PIPELINE_TEST_FFMPEG")
FFPROBE = os.environ.get("PIPELINE_TEST_FFPROBE")


@unittest.skipUnless(
    RUN_MEDIA_TESTS and FFMPEG and FFPROBE,
    "Set PIPELINE_RUN_MEDIA_TESTS=1 and local FFmpeg/FFprobe paths.",
)
class PipelineIntegrationTests(unittest.TestCase):
    def create_source(
        self, path: Path, color: str, frequency: int, *, duration: float = 6
    ) -> None:
        completed = subprocess.run(
            [
                str(FFMPEG),
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c={color}:s=160x90:r=10:d={duration}",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency={frequency}:sample_rate=44100:duration={duration}",
                "-shortest",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                str(path),
            ],
            check=False,
            capture_output=True,
            text=True,
            shell=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def create_project(
        self,
        root: Path,
        *,
        renderer: str,
        segment_duration: float = 1,
        title_duration: float = 0.5,
    ) -> tuple[Path, Path, Path]:
        for folder in ("config", "edl", "input"):
            (root / folder).mkdir(parents=True)
        main_duration = segment_duration * 4
        source_duration = main_duration + 2
        expected_duration = main_duration + (title_duration * 2)
        self.create_source(
            root / "input" / "a.mp4", "blue", 440, duration=source_duration
        )
        self.create_source(
            root / "input" / "b.mp4", "green", 660, duration=source_duration
        )
        project = {
            "project": f"integration-{renderer}",
            "master_camera": "a",
            "renderer": renderer,
            "allow_ffmpeg_fallback": True,
            "output": {
                "width": 160,
                "height": 90,
                "fps": 10,
                "video_codec": "libx264",
                "audio_codec": "aac",
            },
            "duration_policy": {
                "min_seconds": expected_duration - 0.5,
                "max_seconds": expected_duration + 0.5,
                "includes_title_and_credits": True,
            },
            "title": {"text": "Integration Title", "duration": title_duration},
            "credits": {"text": "Integration Credits", "duration": title_duration},
            "cameras": [
                {"id": "a", "path": "input/a.mp4"},
                {"id": "b", "path": "input/b.mp4"},
            ],
        }
        sync = {
            "master_camera": "a",
            "clap_timestamps": {"a": 0.5, "b": 0.5},
            "verification_threshold_ms": 100,
        }
        edl = {
            "project": f"integration-{renderer}",
            "timeline": [
                {
                    "id": "s1",
                    "start": 0,
                    "end": segment_duration,
                    "camera": "a",
                    "reason": "Blue opening",
                    "action": "fade_in",
                },
                {
                    "id": "s2",
                    "start": segment_duration,
                    "end": segment_duration * 2,
                    "camera": "b",
                    "reason": "Green detail",
                    "action": "cut",
                    "overlay": {
                        "type": "lower_third",
                        "text": "Synthetic Fixture",
                        "start": segment_duration + min(0.1, segment_duration * 0.1),
                        "end": (segment_duration * 2)
                        - min(0.2, segment_duration * 0.2),
                        "position": "bottom",
                    },
                },
                {
                    "id": "s3",
                    "start": segment_duration * 2,
                    "end": segment_duration * 3,
                    "camera": "a",
                    "reason": "Blue return",
                    "action": "cut",
                },
                {
                    "id": "s4",
                    "start": segment_duration * 3,
                    "end": segment_duration * 4,
                    "camera": "b",
                    "reason": "Green ending",
                    "action": "fade_to_black",
                },
            ],
        }
        config_path = root / "config" / "project.json"
        sync_path = root / "config" / "sync.json"
        edl_path = root / "edl" / "editing_decisions.json"
        config_path.write_text(json.dumps(project), encoding="utf-8")
        sync_path.write_text(json.dumps(sync), encoding="utf-8")
        edl_path.write_text(json.dumps(edl), encoding="utf-8")
        return config_path, sync_path, edl_path

    def test_moviepy_produces_valid_atomic_draft_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = self.create_project(root, renderer="moviepy")
            prepared = prepare_pipeline(*paths, ffprobe_executable=FFPROBE)
            result, metadata, evidence = render_draft(
                prepared,
                ffmpeg_executable=FFMPEG,
                ffprobe_executable=FFPROBE,
            )
            self.assertEqual(result.backend, "moviepy")
            self.assertTrue(result.output_path.is_file())
            self.assertIn("output\\draft", str(result.output_path))
            self.assertTrue(metadata.has_video)
            self.assertTrue(metadata.has_audio)
            self.assertAlmostEqual(metadata.duration_seconds, 5, delta=0.75)
            self.assertTrue(evidence.is_file())
            report = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertEqual(
                {
                    "common_overlap_duration",
                    "total_event_coverage",
                    "maximum_renderable_duration",
                },
                set(report["duration_metrics"]) - {"presentation_duration"},
            )
            self.assertFalse(list((root / "temp").glob("*.partial.mp4")))
            review_path = root / "evidence" / "approvals" / "review.json"
            record_review(
                project=prepared.config.project,
                draft_path=result.output_path,
                reviewer="Integration Test Reviewer",
                decision="approved",
                comments="Synthetic workflow verification.",
                checklist={item: True for item in REVIEW_CHECKLIST_ITEMS},
                record_path=review_path,
            )
            final = promote_approved_draft(
                draft_path=result.output_path,
                review_record_path=review_path,
                final_directory=root / "output" / "final",
            )
            self.assertEqual(final.read_bytes(), result.output_path.read_bytes())

    def test_deliberate_moviepy_failure_uses_real_ffmpeg_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = self.create_project(root, renderer="moviepy")
            prepared = prepare_pipeline(*paths, ffprobe_executable=FFPROBE)
            with patch(
                "src.moviepy_renderer.MoviePyRenderer.render",
                side_effect=MoviePyRenderError("deliberate integration fallback"),
            ):
                result, metadata, evidence = render_draft(
                    prepared,
                    ffmpeg_executable=FFMPEG,
                    ffprobe_executable=FFPROBE,
                )
            self.assertEqual(result.backend, "ffmpeg")
            self.assertIn(
                "deliberate integration fallback", result.fallback_reason or ""
            )
            self.assertTrue(metadata.has_video)
            self.assertTrue(metadata.has_audio)
            report = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertTrue(report["fallback_activated"])
            self.assertEqual(report["renderer_used"], "ffmpeg")
            self.assertTrue((root / "evidence" / "logs").glob("*.json"))

    @unittest.skipUnless(
        RUN_LONG_MEDIA_TESTS,
        "Set PIPELINE_RUN_LONG_MEDIA_TESTS=1 for the 72-second contract render.",
    )
    def test_ffmpeg_output_meets_default_60_to_180_second_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = self.create_project(
                root,
                renderer="ffmpeg",
                segment_duration=16,
                title_duration=4,
            )
            prepared = prepare_pipeline(*paths, ffprobe_executable=FFPROBE)
            result, metadata, evidence = render_draft(
                prepared,
                ffmpeg_executable=FFMPEG,
                ffprobe_executable=FFPROBE,
            )
            self.assertEqual(result.backend, "ffmpeg")
            self.assertGreaterEqual(metadata.duration_seconds, 60)
            self.assertLessEqual(metadata.duration_seconds, 180)
            self.assertAlmostEqual(metadata.duration_seconds, 72, delta=0.75)
            report = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertEqual(report["camera_switch_count"], 3)
            self.assertTrue(report["output_sha256"])

    @unittest.skipUnless(
        RUN_LONG_MEDIA_TESTS,
        "Set PIPELINE_RUN_LONG_MEDIA_TESTS=1 for automatic 90-second workflow.",
    )
    def test_automatic_synthetic_clap_workflow_renders_compliant_draft(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "input"
            input_path.mkdir()

            def create_event_source(
                path: Path, color: str, transient_times: tuple[float, ...]
            ) -> None:
                transients = "+".join(
                    f"if(between(t\\,{cue}\\,{cue + 0.03})\\,0.9\\,0)"
                    for cue in transient_times
                )
                audio = f"aevalsrc=0.01*sin(2*PI*440*t)+{transients}:s=8000:d=92"
                completed = subprocess.run(
                    [
                        str(FFMPEG),
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-y",
                        "-f",
                        "lavfi",
                        "-i",
                        f"color=c={color}:s=160x90:r=10:d=92",
                        "-f",
                        "lavfi",
                        "-i",
                        audio,
                        "-shortest",
                        "-c:v",
                        "libx264",
                        "-preset",
                        "ultrafast",
                        "-pix_fmt",
                        "yuv420p",
                        "-c:a",
                        "aac",
                        str(path),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    shell=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)

            camera_a = input_path / "AlphaTake.mp4"
            camera_b = input_path / "摄像机B.mov"
            unrelated = input_path / "unrelated_source.mp4"
            create_event_source(camera_a, "blue", (1.0, 22.0, 42.0))
            create_event_source(camera_b, "green", (1.3, 22.3, 42.3))
            create_event_source(unrelated, "red", (3.0, 17.0, 37.0))
            shutil.copy2(camera_a, input_path / "automatic_final.mp4")
            with patch(
                "src.moviepy_renderer.MoviePyRenderer.render",
                side_effect=MoviePyRenderError(
                    "deliberate synthetic automatic fallback"
                ),
            ):
                result, prepared, rendered = run_automatic(
                    project_root=root,
                    input_path=input_path,
                    requested_duration_seconds=90,
                    title="Synthetic Kindergarten Graduation",
                    credits="Edited by Synthetic Team | BTIS3053",
                    credits_duration=3,
                    ffmpeg_executable=FFMPEG,
                    ffprobe_executable=FFPROBE,
                )
            self.assertEqual(
                result.outcome,
                AutomationOutcome.DRAFT_RENDERED_WITH_UNVERIFIED_SYNC,
            )
            self.assertIsNotNone(prepared)
            self.assertEqual(
                prepared.plan.credits.text, "Edited by Synthetic Team | BTIS3053"
            )
            self.assertEqual(prepared.plan.credits.duration, 3.0)
            generated_project = json.loads(
                (root / "config" / "generated_project.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                generated_project["credits"],
                {
                    "text": "Edited by Synthetic Team | BTIS3053",
                    "duration": 3,
                },
            )
            self.assertEqual(result.analysed_pair_count, 3)
            self.assertEqual(result.excluded_derived_count, 1)
            self.assertEqual(
                {Path(path).name for path in result.selected_camera_paths},
                {camera_a.name, camera_b.name},
            )
            grouping = json.loads(
                (root / "evidence" / "reports" / "camera_grouping.json").read_text(
                    encoding="utf-8"
                )
            )
            relevant_pair = next(
                pair
                for pair in grouping["pairs"]
                if {Path(pair["path_a"]).name, Path(pair["path_b"]).name}
                == {camera_a.name, camera_b.name}
            )
            self.assertTrue(relevant_pair["accepted"])
            self.assertAlmostEqual(
                abs(relevant_pair["estimated_offset_seconds"]), 0.3, delta=0.08
            )
            self.assertTrue(
                all(unrelated.name not in path for path in grouping["selected_paths"])
            )
            self.assertTrue((root / "config" / "generated_project.json").is_file())
            self.assertTrue(
                (root / "edl" / "generated_editing_decisions.json").is_file()
            )
            self.assertIsNotNone(rendered)
            render_result, metadata, evidence_path = rendered
            self.assertEqual(render_result.backend, "ffmpeg")
            self.assertGreaterEqual(metadata.duration_seconds, 60)
            self.assertLessEqual(metadata.duration_seconds, 180)
            self.assertAlmostEqual(metadata.duration_seconds, 90, delta=0.75)
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            self.assertEqual(evidence["camera_switch_count"], 6)
            self.assertEqual(
                evidence["synchronisation"]["acceptance_status"],
                "needs_human_confirmation",
            )
            self.assertFalse(list((root / "output" / "final").glob("*")))


if __name__ == "__main__":
    unittest.main()
