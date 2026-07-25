"""Thin command-line entry point for the local editing pipeline."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import replace
from pathlib import Path

from .auto_pipeline import prepare_automatic, run_automatic
from .camera_grouping import group_camera_sources
from .edl_generator import generate_edl
from .errors import PipelineError, PreparationError
from .logging_config import configure_logging
from .media_probe import probe_cameras
from .models import CameraSource
from .pipeline import prepare_pipeline, render_draft
from .preflight import check_dependencies, require_dependencies
from .render_plan import format_render_plan
from .review import (
    create_review_checklist,
    load_checklist,
    promote_approved_draft,
    record_review,
)
from .sync import apply_sync, load_sync_config
from .sync_assistant import analyse_sync, confirm_sync_timestamp
from .validate_inputs import load_project_config
from .video_discovery import discover_videos

LOGGER = logging.getLogger(__name__)


def _add_pipeline_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", type=Path, default=Path("config/project.json"))
    parser.add_argument("--sync", type=Path, default=Path("config/sync.json"))
    parser.add_argument("--edl", type=Path, default=Path("edl/editing_decisions.json"))
    parser.add_argument("--ffprobe", type=Path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Local, deterministic, EDL-driven multi-camera graduation video pipeline."
        )
    )
    parser.add_argument("--verbose", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect = subparsers.add_parser(
        "inspect", help="Discover and probe local source-video candidates."
    )
    inspect.add_argument("--input", type=Path, default=Path("input"))
    inspect.add_argument("--ffprobe", type=Path)
    inspect.add_argument("--include-derived", action="store_true")
    inspect.add_argument(
        "--report", type=Path, default=Path("evidence/reports/video_discovery.json")
    )

    detect_sync = subparsers.add_parser(
        "detect-sync", help="Suggest local audio sync cues for human verification."
    )
    detect_sync.add_argument("--input", type=Path, default=Path("input"))
    detect_sync.add_argument("--config", type=Path)
    detect_sync.add_argument(
        "--output", type=Path, default=Path("config/generated_sync.json")
    )
    detect_sync.add_argument(
        "--report", type=Path, default=Path("evidence/reports/sync_candidates.json")
    )
    detect_sync.add_argument("--search-window", type=float, default=15.0)
    detect_sync.add_argument("--ffmpeg", type=Path)
    detect_sync.add_argument("--ffprobe", type=Path)
    detect_sync.add_argument("--overwrite", action="store_true")
    detect_sync.add_argument("--camera-file", type=Path, action="append", default=[])

    confirm_sync = subparsers.add_parser(
        "confirm-sync", help="Record one human-verified clap timestamp."
    )
    confirm_sync.add_argument(
        "--sync", type=Path, default=Path("config/generated_sync.json")
    )
    confirm_sync.add_argument("--camera", required=True)
    confirm_sync.add_argument("--timestamp", type=float, required=True)

    generate = subparsers.add_parser(
        "generate-edl", help="Generate a deterministic rule-based EDL proposal."
    )
    generate.add_argument(
        "--config", type=Path, default=Path("config/generated_project.json")
    )
    generate.add_argument(
        "--sync", type=Path, default=Path("config/generated_sync.json")
    )
    generate.add_argument("--duration", type=float, required=True)
    generate.add_argument(
        "--output",
        type=Path,
        default=Path("edl/generated_editing_decisions.json"),
    )
    generate.add_argument("--allow-smoke", action="store_true")
    generate.add_argument("--overwrite", action="store_true")
    generate.add_argument("--ffprobe", type=Path)

    def add_automatic_arguments(command: argparse.ArgumentParser) -> None:
        command.add_argument("--input", type=Path, default=Path("input"))
        command.add_argument("--duration", type=float, default=90.0)
        command.add_argument("--title", default="Kindergarten Graduation Ceremony")
        command.add_argument("--search-window", type=float, default=15.0)
        command.add_argument("--allow-smoke", action="store_true")
        command.add_argument("--include-derived", action="store_true")
        command.add_argument("--overwrite", action="store_true")
        command.add_argument("--ffmpeg", type=Path)
        command.add_argument("--ffprobe", type=Path)
        command.add_argument("--camera-file", type=Path, action="append", default=[])

    prepare = subparsers.add_parser(
        "prepare", help="Discover, analyse sync, generate, and validate artefacts."
    )
    add_automatic_arguments(prepare)
    auto = subparsers.add_parser(
        "auto", help="Prepare and safely render a draft; never approve it."
    )
    add_automatic_arguments(auto)

    preflight = subparsers.add_parser(
        "preflight", help="Check local renderer dependencies."
    )
    preflight.add_argument("--config", type=Path, default=Path("config/project.json"))
    preflight.add_argument("--ffmpeg", type=Path)
    preflight.add_argument("--ffprobe", type=Path)

    validate = subparsers.add_parser(
        "validate", help="Validate files, sync, EDL, and print the render plan."
    )
    _add_pipeline_arguments(validate)

    render = subparsers.add_parser(
        "render", help="Render, validate, and atomically publish a draft MP4."
    )
    _add_pipeline_arguments(render)
    render.add_argument("--ffmpeg", type=Path)

    template = subparsers.add_parser(
        "review-template", help="Create a checklist for complete human review."
    )
    template.add_argument("--draft", type=Path, required=True)
    template.add_argument(
        "--output", type=Path, default=Path("evidence/approvals/review_checklist.json")
    )

    review = subparsers.add_parser(
        "review", help="Record a human decision bound to the current draft checksum."
    )
    review.add_argument("--project", required=True)
    review.add_argument("--draft", type=Path, required=True)
    review.add_argument("--reviewer", required=True)
    review.add_argument(
        "--decision", choices=("approved", "changes_requested"), required=True
    )
    review.add_argument("--comments", default="")
    review.add_argument("--checklist", type=Path, required=True)
    review.add_argument(
        "--output", type=Path, default=Path("evidence/approvals/review_record.json")
    )

    approve = subparsers.add_parser(
        "approve", help="Promote an unchanged, approved draft to output/final."
    )
    approve.add_argument("--draft", type=Path, required=True)
    approve.add_argument("--review-record", type=Path, required=True)
    approve.add_argument("--final-dir", type=Path, default=Path("output/final"))
    return parser


def run(args: argparse.Namespace) -> int:
    project_root = Path.cwd()
    if args.command == "inspect":
        report = discover_videos(
            args.input,
            project_root=project_root,
            ffprobe_executable=args.ffprobe,
            include_derived=args.include_derived,
            report_path=args.report,
        )
        print(f"Discovered videos: {len(report.videos)}")
        print(f"Usable camera candidates: {len(report.usable_videos)}")
        for video in report.videos:
            identity = video.camera_id or "-"
            print(
                f"{identity}: {video.relative_path} [{video.classification}] "
                f"{video.duration_seconds if video.duration_seconds is not None else 'n/a'}s"
            )
        print(f"Discovery report: {args.report}")
        return 0

    if args.command == "detect-sync":
        if args.config:
            config = load_project_config(args.config)
            cameras = probe_cameras(config.cameras, ffprobe_executable=args.ffprobe)
            master_camera = config.master_camera
        else:
            discovery = discover_videos(
                args.input,
                project_root=project_root,
                ffprobe_executable=args.ffprobe,
            )
            grouping = group_camera_sources(
                discovery.videos,
                input_path=args.input,
                ffmpeg_executable=args.ffmpeg,
                explicit_camera_files=tuple(args.camera_file),
                report_path=Path("evidence/reports/camera_grouping.json"),
            )
            group = grouping.selected_videos
            if len(group) < 2:
                raise PreparationError(
                    f"No related camera group could be established safely after "
                    f"{grouping.analysed_pair_count} pair analyses. "
                    f"{grouping.reason}"
                )
            cameras = tuple(
                CameraSource(
                    item.camera_id,
                    item.path,
                    duration_seconds=item.duration_seconds,
                    has_audio=item.has_audio,
                )
                for item in group
                if item.camera_id
            )
            master_camera = cameras[0].id
        analyses, _ = analyse_sync(
            cameras,
            master_camera=master_camera,
            search_window_seconds=args.search_window,
            ffmpeg_executable=args.ffmpeg,
            sync_path=args.output,
            report_path=args.report,
            overwrite=args.overwrite,
        )
        for item in analyses:
            value = (
                f"{item.selected_timestamp_seconds:.3f}s"
                if item.selected_timestamp_seconds is not None
                else "none"
            )
            print(
                f"{item.camera_id}: {item.state}; selected={value}; "
                f"confidence={item.confidence:.3f}; human verification required"
            )
        print(f"Generated sync: {args.output}")
        print(f"Detailed report: {args.report}")
        return 0

    if args.command == "confirm-sync":
        payload = confirm_sync_timestamp(
            args.sync,
            camera_id=args.camera,
            timestamp_seconds=args.timestamp,
        )
        print(f"Recorded human confirmation for {args.camera}: {args.timestamp:.3f}s")
        print(f"Sync status: {payload['acceptance_status']}")
        return 0

    if args.command == "generate-edl":
        config = load_project_config(args.config)
        probed = probe_cameras(config.cameras, ffprobe_executable=args.ffprobe)
        sync = load_sync_config(args.sync)
        synced = apply_sync(probed, sync, expected_master_camera=config.master_camera)
        config = replace(config, cameras=synced)
        edl, metadata = generate_edl(
            config,
            requested_duration_seconds=args.duration,
            allow_smoke=args.allow_smoke,
            output_path=args.output,
            report_path=Path("evidence/reports/generated_edl.json"),
            overwrite=args.overwrite,
        )
        print(f"Generated EDL: {args.output}")
        print(f"Segments: {len(edl.timeline)}")
        print(f"Camera switches: {edl.switch_count}")
        print(
            "Expected duration: "
            f"{float(metadata['expected_output_duration_seconds']):.3f}s"
        )
        print("Human review required: yes")
        return 0

    if args.command in {"prepare", "auto"}:
        options = {
            "project_root": project_root,
            "input_path": args.input,
            "requested_duration_seconds": args.duration,
            "title": args.title,
            "ffmpeg_executable": args.ffmpeg,
            "ffprobe_executable": args.ffprobe,
            "search_window_seconds": args.search_window,
            "allow_smoke": args.allow_smoke,
            "include_derived": args.include_derived,
            "overwrite": args.overwrite,
            "camera_files": tuple(args.camera_file),
        }
        if args.command == "prepare":
            result = prepare_automatic(**options)
            rendered = None
        else:
            result, _, rendered = run_automatic(**options)
        print(f"Discovered videos: {result.discovered_count}")
        print(f"Usable camera candidates: {result.usable_camera_count}")
        print(f"Excluded derived outputs: {result.excluded_derived_count}")
        print(f"Analysed camera pairs: {result.analysed_pair_count}")
        print(f"Camera group state: {result.camera_group_state}")
        print(
            "Best camera group score: "
            + (
                f"{result.camera_group_score:.3f}"
                if result.camera_group_score is not None
                else "n/a"
            )
        )
        print(
            "Selected camera group: "
            + (", ".join(result.selected_camera_paths) or "none")
        )
        print(f"Master camera: {result.master_camera or 'none'}")
        print(f"Outcome: {result.outcome.value}")
        print(f"Sync status: {result.sync_status}")
        print(f"Requested duration: {result.requested_duration_seconds:.3f} seconds")
        maximum = result.maximum_honest_duration_seconds
        print(
            "Maximum honest common duration: "
            + (f"{maximum:.3f} seconds" if maximum is not None else "unknown")
        )
        print(f"Generated project: {result.project_path or 'none'}")
        print(f"Generated sync report: {result.sync_path or 'none'}")
        print(f"Generated EDL: {result.edl_path or 'none'}")
        if rendered is not None:
            print(f"Draft: {rendered[0].output_path}")
            print(f"Evidence: {rendered[2]}")
        else:
            print("Draft: none")
        for warning in result.warnings:
            print(f"Warning: {warning}")
        print("Human review required: yes")
        print("Final approval performed: no")
        return 0 if args.command == "prepare" or rendered is not None else 1

    if args.command == "preflight":
        config = load_project_config(args.config, require_camera_files=False)
        report = check_dependencies(
            config.renderer,
            allow_ffmpeg_fallback=config.allow_ffmpeg_fallback,
            ffmpeg_path=args.ffmpeg,
            ffprobe_path=args.ffprobe,
        )
        print(json.dumps(report.to_dict(), indent=2))
        return 0 if report.selected_renderer_ready else 1

    if args.command in {"validate", "render"}:
        config = load_project_config(args.config)
        report = check_dependencies(
            config.renderer,
            allow_ffmpeg_fallback=config.allow_ffmpeg_fallback,
            ffmpeg_path=getattr(args, "ffmpeg", None),
            ffprobe_path=args.ffprobe,
        )
        require_dependencies(report)
        prepared = prepare_pipeline(
            args.config,
            args.sync,
            args.edl,
            ffprobe_executable=args.ffprobe or report.ffprobe_path,
        )
        print(format_render_plan(prepared.plan))
        if args.command == "validate":
            print("Validation succeeded; no media was rendered.")
            return 0
        result, metadata, evidence_path = render_draft(
            prepared,
            ffmpeg_executable=args.ffmpeg or report.ffmpeg_path,
            ffprobe_executable=args.ffprobe or report.ffprobe_path,
        )
        print(f"Draft: {result.output_path}")
        print(f"Renderer used: {result.backend}")
        if result.fallback_reason:
            print(f"Fallback reason: {result.fallback_reason}")
        print(f"Duration: {metadata.duration_seconds:.3f}s")
        print(f"Evidence: {evidence_path}")
        return 0

    if args.command == "review-template":
        create_review_checklist(args.output, draft_path=args.draft)
        print(f"Review checklist created: {args.output}")
        return 0

    if args.command == "review":
        checklist = load_checklist(args.checklist)
        record = record_review(
            project=args.project,
            draft_path=args.draft,
            reviewer=args.reviewer,
            decision=args.decision,
            comments=args.comments,
            checklist=checklist,
            record_path=args.output,
        )
        print(f"Review recorded: {args.output}")
        print(f"Decision: {record.decision}")
        print(f"Draft SHA-256: {record.draft_sha256}")
        return 0

    if args.command == "approve":
        final_path = promote_approved_draft(
            draft_path=args.draft,
            review_record_path=args.review_record,
            final_directory=args.final_dir,
        )
        print(f"Approved final: {final_path}")
        return 0

    raise AssertionError(f"Unhandled command: {args.command}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    configure_logging(verbose=args.verbose)
    try:
        return run(args)
    except PipelineError as exc:
        LOGGER.error("%s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
