"""Deterministic local video discovery and conservative camera grouping."""

from __future__ import annotations

import re
from dataclasses import asdict, replace
from pathlib import Path

from .evidence import utc_now
from .json_utils import write_json_atomic
from .media_probe import probe_video
from .models import (
    SUPPORTED_VIDEO_EXTENSIONS,
    DiscoveredVideo,
    DiscoveryReport,
)

EXCLUDED_DIRECTORY_NAMES = frozenset({"output", "temp", "evidence"})
DERIVED_NAME_MARKERS = ("draft", "final", "rendered", "output")


def _relative(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _is_in_excluded_directory(path: Path, input_root: Path) -> bool:
    try:
        relative = path.relative_to(input_root)
    except ValueError:
        return True
    return any(
        part.casefold() in EXCLUDED_DIRECTORY_NAMES for part in relative.parts[:-1]
    )


def _is_derived_name(path: Path) -> bool:
    name = path.stem.casefold()
    return any(marker in name for marker in DERIVED_NAME_MARKERS)


def _sort_key(path: Path, input_root: Path) -> tuple[str, str]:
    relative = path.relative_to(input_root).as_posix()
    return relative.casefold(), relative


def discover_videos(
    input_path: Path,
    *,
    project_root: Path,
    ffprobe_executable: str | Path | None = None,
    include_derived: bool = False,
    report_path: Path | None = None,
) -> DiscoveryReport:
    """Discover and probe supported media without changing any source file."""
    input_root = input_path.resolve()
    if not input_root.is_dir():
        from .errors import InputFileError

        raise InputFileError(f"Discovery input is not a local directory: {input_path}")

    paths = sorted(
        (
            path
            for path in input_root.rglob("*")
            if path.is_file()
            and path.suffix.casefold() in SUPPORTED_VIDEO_EXTENSIONS
            and not _is_in_excluded_directory(path, input_root)
        ),
        key=lambda path: _sort_key(path, input_root),
    )
    videos: list[DiscoveredVideo] = []
    usable_index = 0
    for path in paths:
        relative_path = _relative(path, project_root)
        if _is_derived_name(path) and not include_derived:
            videos.append(
                DiscoveredVideo(
                    camera_id=None,
                    path=path,
                    relative_path=relative_path,
                    duration_seconds=None,
                    width=None,
                    height=None,
                    display_rotation=0,
                    fps=None,
                    video_codec=None,
                    has_audio=None,
                    audio_codec=None,
                    classification="likely_derived_output",
                    usable=False,
                    warnings=("Excluded by generated/derived filename policy.",),
                )
            )
            continue
        try:
            metadata = probe_video(path, ffprobe_executable=ffprobe_executable)
        except Exception as exc:
            from .errors import MediaProbeError

            if not isinstance(exc, MediaProbeError):
                raise
            videos.append(
                DiscoveredVideo(
                    camera_id=None,
                    path=path,
                    relative_path=relative_path,
                    duration_seconds=None,
                    width=None,
                    height=None,
                    display_rotation=0,
                    fps=None,
                    video_codec=None,
                    has_audio=None,
                    audio_codec=None,
                    classification="unreadable_media",
                    usable=False,
                    warnings=(str(exc),),
                )
            )
            continue
        usable_index += 1
        warnings: list[str] = []
        if not metadata.has_audio:
            warnings.append(
                "No audio stream; audio-based sync assistance is unavailable."
            )
        videos.append(
            DiscoveredVideo(
                camera_id=f"camera_{usable_index:02d}",
                path=path,
                relative_path=relative_path,
                duration_seconds=metadata.duration_seconds,
                width=metadata.width,
                height=metadata.height,
                display_rotation=metadata.display_rotation,
                fps=metadata.fps,
                video_codec=metadata.video_codec,
                has_audio=metadata.has_audio,
                audio_codec=metadata.audio_codec,
                classification="likely_source",
                usable=True,
                warnings=tuple(warnings),
            )
        )

    report = DiscoveryReport(input_root, tuple(videos), report_path)
    if report_path is not None:
        payload = {
            "generated_at": utc_now(),
            "input_path": _relative(input_root, project_root),
            "processing": "local-only metadata inspection",
            "supported_extensions": sorted(SUPPORTED_VIDEO_EXTENSIONS),
            "include_derived": include_derived,
            "videos": [
                {
                    **asdict(video),
                    "path": video.relative_path,
                }
                for video in videos
            ],
            "usable_camera_count": len(report.usable_videos),
        }
        write_json_atomic(report_path, payload)
    return report


def _event_tokens(path: Path) -> set[str]:
    """Return long date/time-like tokens used only for conservative grouping."""
    stem = path.stem.casefold()
    tokens = set(re.findall(r"(?<!\d)\d{12,14}(?!\d)", stem))
    compact = re.sub(r"\D", "", stem)
    if len(compact) >= 14:
        tokens.add(compact[:14])
    return tokens


def select_related_camera_group(
    videos: tuple[DiscoveredVideo, ...],
) -> tuple[DiscoveredVideo, ...]:
    """Select a deterministic group only when filenames share event-time evidence."""
    usable = [video for video in videos if video.usable]
    groups: dict[str, list[DiscoveredVideo]] = {}
    for video in usable:
        for token in _event_tokens(video.path):
            groups.setdefault(token, []).append(video)
    valid_groups = [
        group for group in groups.values() if len({video.path for video in group}) >= 2
    ]
    if not valid_groups:
        return ()
    valid_groups.sort(
        key=lambda group: (
            -len({video.path for video in group}),
            -min(video.duration_seconds or 0 for video in group),
            tuple(video.relative_path.casefold() for video in group),
        )
    )
    unique: dict[Path, DiscoveredVideo] = {}
    for video in valid_groups[0]:
        unique[video.path] = video
    return tuple(sorted(unique.values(), key=lambda item: item.camera_id or "")[:4])


def with_report_path(report: DiscoveryReport, path: Path) -> DiscoveryReport:
    return replace(report, report_path=path)
