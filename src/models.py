"""Typed data contracts shared by the pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Literal

SUPPORTED_ACTIONS = frozenset({"cut", "fade_in", "fade_out", "fade_to_black"})
SUPPORTED_OVERLAY_TYPES = frozenset({"lower_third", "label", "subtitle"})
SUPPORTED_RENDERERS = frozenset({"moviepy", "ffmpeg"})
SUPPORTED_VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".mkv"})


@dataclass(frozen=True)
class CameraSource:
    id: str
    path: Path
    clap_time_seconds: float | None = None
    offset_seconds: float = 0.0
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    has_audio: bool | None = None
    video_codec: str | None = None
    audio_codec: str | None = None


@dataclass(frozen=True)
class TextSpec:
    text: str
    duration: float


@dataclass(frozen=True)
class OutputSpec:
    width: int = 1280
    height: int = 720
    fps: int = 30
    video_codec: str = "libx264"
    audio_codec: str = "aac"


@dataclass(frozen=True)
class DurationPolicy:
    min_seconds: float = 60.0
    max_seconds: float = 180.0
    includes_title_and_credits: bool = True


@dataclass(frozen=True)
class ProjectConfig:
    project: str
    master_camera: str
    renderer: Literal["moviepy", "ffmpeg"]
    allow_ffmpeg_fallback: bool
    output: OutputSpec
    title: TextSpec
    credits: TextSpec
    cameras: tuple[CameraSource, ...]
    duration_policy: DurationPolicy = field(default_factory=DurationPolicy)


@dataclass(frozen=True)
class SyncConfig:
    master_camera: str
    clap_timestamps: dict[str, float]
    verification_threshold_ms: int = 100
    cue_type: str = "manual_clap"
    cue_description: str | None = None
    acceptance_status: str = "verified"


@dataclass(frozen=True)
class OverlaySpec:
    type: Literal["lower_third", "label", "subtitle"]
    text: str
    start: float | None = None
    end: float | None = None
    position: str | None = "bottom"


@dataclass(frozen=True)
class EDLSegment:
    id: str
    start: float
    end: float
    camera: str
    reason: str
    action: Literal["cut", "fade_in", "fade_out", "fade_to_black"]
    overlay: OverlaySpec | None = None

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass(frozen=True)
class EDL:
    project: str
    timeline: tuple[EDLSegment, ...]

    @property
    def main_duration_seconds(self) -> float:
        return sum(segment.duration for segment in self.timeline)

    @property
    def switch_count(self) -> int:
        return sum(
            current.camera != previous.camera
            for previous, current in zip(self.timeline, self.timeline[1:])
        )


@dataclass(frozen=True)
class MediaMetadata:
    path: Path
    duration_seconds: float
    width: int
    height: int
    fps: float
    has_video: bool
    has_audio: bool
    video_codec: str | None = None
    audio_codec: str | None = None
    display_rotation: int = 0


@dataclass(frozen=True)
class RenderInstruction:
    segment_id: str
    source_path: Path
    master_start: float
    master_end: float
    source_start: float
    source_end: float
    camera_id: str
    action: str
    reason: str
    overlay: OverlaySpec | None
    has_audio: bool

    @property
    def duration(self) -> float:
        return self.source_end - self.source_start


@dataclass(frozen=True)
class RenderPlan:
    project: str
    title: TextSpec
    credits: TextSpec
    output: OutputSpec
    duration_policy: DurationPolicy
    instructions: tuple[RenderInstruction, ...]
    expected_duration_seconds: float
    renderer: str
    allow_ffmpeg_fallback: bool
    camera_offsets: dict[str, float]

    @property
    def switch_count(self) -> int:
        return sum(
            current.camera_id != previous.camera_id
            for previous, current in zip(self.instructions, self.instructions[1:])
        )


@dataclass(frozen=True)
class RenderResult:
    output_path: Path
    backend: str
    started_at: str
    completed_at: str
    duration_seconds: float
    warnings: tuple[str, ...] = ()
    command_log_path: Path | None = None
    fallback_reason: str | None = None


@dataclass(frozen=True)
class ReviewRecord:
    project: str
    draft_path: str
    draft_sha256: str
    reviewer: str
    decision: Literal["approved", "changes_requested"]
    comments: str
    reviewed_at: str
    checklist: dict[str, bool]


class AutomationOutcome(str, Enum):
    READY_FOR_DRAFT = "READY_FOR_DRAFT"
    READY_FOR_SMOKE_ONLY = "READY_FOR_SMOKE_ONLY"
    NEEDS_CAMERA_SELECTION = "NEEDS_CAMERA_SELECTION"
    NEEDS_SYNC_CONFIRMATION = "NEEDS_SYNC_CONFIRMATION"
    INSUFFICIENT_COMMON_DURATION = "INSUFFICIENT_COMMON_DURATION"
    INVALID_INPUT = "INVALID_INPUT"
    DRAFT_RENDERED = "DRAFT_RENDERED"
    DRAFT_RENDERED_WITH_UNVERIFIED_SYNC = "DRAFT_RENDERED_WITH_UNVERIFIED_SYNC"


@dataclass(frozen=True)
class DiscoveredVideo:
    camera_id: str | None
    path: Path
    relative_path: str
    duration_seconds: float | None
    width: int | None
    height: int | None
    display_rotation: int
    fps: float | None
    video_codec: str | None
    has_audio: bool | None
    audio_codec: str | None
    classification: str
    usable: bool
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class DiscoveryReport:
    input_path: Path
    videos: tuple[DiscoveredVideo, ...]
    report_path: Path | None = None

    @property
    def usable_videos(self) -> tuple[DiscoveredVideo, ...]:
        return tuple(video for video in self.videos if video.usable)


@dataclass(frozen=True)
class SyncCandidate:
    timestamp_seconds: float
    confidence: float
    cue_type: str
    supporting_metric: float


@dataclass(frozen=True)
class CameraSyncAnalysis:
    camera_id: str
    candidates: tuple[SyncCandidate, ...]
    selected_timestamp_seconds: float | None
    confidence: float
    state: str
    requires_human_verification: bool
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class PreparationResult:
    outcome: AutomationOutcome
    discovered_count: int
    usable_camera_count: int
    master_camera: str | None
    sync_status: str
    requested_duration_seconds: float
    maximum_honest_duration_seconds: float | None
    project_path: Path | None
    sync_path: Path | None
    edl_path: Path | None
    summary_path: Path
    render_permitted: bool
    smoke: bool
    warnings: tuple[str, ...] = ()
