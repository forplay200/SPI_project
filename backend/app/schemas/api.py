"""Typed request and response contracts for the local UI API."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    DISCOVERING = "DISCOVERING"
    PROBING_MEDIA = "PROBING_MEDIA"
    GROUPING_CAMERAS = "GROUPING_CAMERAS"
    ANALYSING_AUDIO = "ANALYSING_AUDIO"
    GENERATING_EDL = "GENERATING_EDL"
    VALIDATING = "VALIDATING"
    RENDERING = "RENDERING"
    VALIDATING_OUTPUT = "VALIDATING_OUTPUT"
    GENERATING_EVIDENCE = "GENERATING_EVIDENCE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


TERMINAL_JOB_STATES = {
    JobStatus.COMPLETED,
    JobStatus.FAILED,
    JobStatus.CANCELLED,
}


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    input_folder: str = "input"
    duration_seconds: float = Field(default=90, gt=0, le=180)
    resolution: Literal["1280x720", "1920x1080"] = "1280x720"
    draft_mode: bool = True
    smoke_mode: bool = False
    credits: str = Field(default="Edited by the Project Team", min_length=1)
    credits_duration: float | None = Field(default=None, gt=0, le=30)

    @field_validator("title", "credits")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    input_folder: str | None = None
    duration_seconds: float | None = Field(default=None, gt=0, le=180)
    resolution: Literal["1280x720", "1920x1080"] | None = None
    draft_mode: bool | None = None
    smoke_mode: bool | None = None
    credits: str | None = Field(default=None, min_length=1)
    credits_duration: float | None = Field(default=None, gt=0, le=30)


class ProjectResponse(ProjectCreate):
    id: str
    created_at: str
    updated_at: str
    outcome: str = "INVALID_INPUT"
    current_step: int = 1
    artifacts: dict[str, str] = Field(default_factory=dict)
    latest_job_id: str | None = None


class JobResponse(BaseModel):
    job_id: str
    project_id: str
    operation: str
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    message: str
    current_step: int
    warning: str | None = None
    error: str | None = None
    result: dict[str, Any] | None = None
    created_at: str
    updated_at: str


class AnalysisResponse(BaseModel):
    videos: list[dict[str, Any]]
    selected_camera_ids: list[str]
    master_camera: str | None
    suggested_camera_ids: list[str] = Field(default_factory=list)
    suggested_master_camera: str | None = None
    grouping: dict[str, Any]
    common_overlap_duration: float | None = None
    total_event_coverage: float | None = None
    maximum_renderable_duration: float | None = None


class CameraGroupUpdate(BaseModel):
    camera_ids: list[str] = Field(min_length=2, max_length=4)
    master_camera: str
    continue_with_human_verification: bool = False


class SyncConfirmRequest(BaseModel):
    camera_id: str
    timestamp_seconds: float = Field(ge=0)
    acknowledge_sync_risk: bool = False


class SyncRejectRequest(BaseModel):
    camera_id: str
    timestamp_seconds: float | None = Field(default=None, ge=0)
    reason: str = Field(default="Rejected by human reviewer", min_length=1)


class EDLUpdateRequest(BaseModel):
    project: str
    timeline: list[dict[str, Any]] = Field(min_length=1)


class ReviewRequest(BaseModel):
    reviewer: str = Field(min_length=1)
    comments: str = ""
    decision: Literal["approved", "changes_requested"] = "changes_requested"
    checklist: dict[str, bool]


class ApprovalEligibility(BaseModel):
    eligible: bool
    blockers: list[str]
    draft_sha256: str | None = None
    review_status: str
    sync_status: str
    compliance_status: str


class EvidenceItem(BaseModel):
    id: str
    label: str
    category: str
    path: str
    media_type: str
    exists: bool


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "kindergarten-video-local-api"
    local_only: bool = True
    timestamp: str = Field(default_factory=utc_now)
