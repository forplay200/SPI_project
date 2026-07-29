"""FastAPI routes exposing the local pipeline as typed workflow operations."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import FileResponse

from backend.app.schemas.api import (
    AnalysisResponse,
    ApprovalEligibility,
    CameraGroupUpdate,
    EDLUpdateRequest,
    EvidenceItem,
    HealthResponse,
    JobResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    ReviewRequest,
    SyncConfirmRequest,
    SyncRejectRequest,
)
from backend.app.services.automation_service import AutomationService
from backend.app.services.job_service import JobNotFoundError, JobService
from backend.app.services.project_service import ProjectNotFoundError, ProjectService
from src.preflight import check_dependencies

router = APIRouter()


def _services(request: Request) -> tuple[ProjectService, JobService, AutomationService]:
    return (
        request.app.state.projects,
        request.app.state.jobs,
        request.app.state.automation,
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@router.get("/preflight")
def preflight() -> dict[str, Any]:
    report = check_dependencies("moviepy", allow_ffmpeg_fallback=True)
    return report.to_dict()


@router.post(
    "/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED
)
def create_project(payload: ProjectCreate, request: Request) -> ProjectResponse:
    projects, _, automation = _services(request)
    automation.path_policy.resolve_input_directory(payload.input_folder)
    return projects.create(payload)


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, request: Request) -> ProjectResponse:
    projects, _, _ = _services(request)
    return projects.get(project_id)


@router.put("/projects/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str, payload: ProjectUpdate, request: Request
) -> ProjectResponse:
    projects, _, automation = _services(request)
    if payload.input_folder is not None:
        automation.path_policy.resolve_input_directory(payload.input_folder)
    return projects.update(project_id, payload)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, request: Request) -> Response:
    projects, _, _ = _services(request)
    projects.delete(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _start_job(
    request: Request,
    project_id: str,
    operation: str,
    handler: Any,
    *,
    step: int,
) -> JobResponse:
    projects, jobs, _ = _services(request)
    projects.get(project_id)
    job = jobs.start(project_id, operation, handler, step=step)
    projects.patch(project_id, latest_job_id=job.job_id, current_step=step)
    return job


@router.post("/projects/{project_id}/analysis", response_model=JobResponse)
def start_analysis(project_id: str, request: Request) -> JobResponse:
    _, _, automation = _services(request)
    return _start_job(
        request,
        project_id,
        "analysis",
        lambda context: automation.analyse(project_id, context),
        step=2,
    )


@router.get("/projects/{project_id}/analysis", response_model=AnalysisResponse)
def get_analysis(project_id: str, request: Request) -> AnalysisResponse:
    _, _, automation = _services(request)
    result = automation.get_analysis(project_id)
    if result is None:
        raise HTTPException(404, "No footage analysis exists for this project.")
    return AnalysisResponse.model_validate(result)


@router.get("/projects/{project_id}/cameras")
def get_cameras(project_id: str, request: Request) -> dict[str, Any]:
    analysis = get_analysis(project_id, request).model_dump()
    return {
        "videos": analysis.get("videos", []),
        "selected_camera_ids": analysis.get("selected_camera_ids", []),
        "master_camera": analysis.get("master_camera"),
        "suggested_camera_ids": analysis.get("suggested_camera_ids", []),
        "suggested_master_camera": analysis.get("suggested_master_camera"),
    }


@router.put("/projects/{project_id}/camera-group")
def update_camera_group(
    project_id: str, payload: CameraGroupUpdate, request: Request
) -> dict[str, Any]:
    _, _, automation = _services(request)
    return automation.select_camera_group(
        project_id,
        payload.camera_ids,
        payload.master_camera,
        continue_with_human_verification=payload.continue_with_human_verification,
    )


@router.post("/projects/{project_id}/sync/detect", response_model=JobResponse)
def start_sync(project_id: str, request: Request) -> JobResponse:
    _, _, automation = _services(request)
    return _start_job(
        request,
        project_id,
        "sync",
        lambda context: automation.detect_sync(project_id, context),
        step=3,
    )


@router.get("/projects/{project_id}/sync")
def get_sync(project_id: str, request: Request) -> dict[str, Any]:
    _, _, automation = _services(request)
    result = automation.get_sync(project_id)
    if result is None:
        raise HTTPException(404, "No synchronisation analysis exists for this project.")
    return result


@router.post("/projects/{project_id}/sync/confirm")
def confirm_sync(
    project_id: str, payload: SyncConfirmRequest, request: Request
) -> dict[str, Any]:
    _, _, automation = _services(request)
    return automation.confirm_sync(
        project_id,
        payload.camera_id,
        payload.timestamp_seconds,
        acknowledge_sync_risk=payload.acknowledge_sync_risk,
    )


@router.post("/projects/{project_id}/sync/reject")
def reject_sync(
    project_id: str, payload: SyncRejectRequest, request: Request
) -> dict[str, Any]:
    _, _, automation = _services(request)
    return automation.reject_sync(
        project_id,
        payload.camera_id,
        payload.timestamp_seconds,
        payload.reason,
    )


@router.get("/projects/{project_id}/sync/preview/{camera_id}")
def sync_preview(project_id: str, camera_id: str, request: Request) -> FileResponse:
    _, _, automation = _services(request)
    path = automation.registered_files(project_id).get(f"camera-{camera_id}")
    if path is None or not path.is_file():
        raise HTTPException(404, "Camera media is not registered for this project.")
    return FileResponse(path, media_type="video/mp4", filename=path.name)


@router.post("/projects/{project_id}/edl/generate", response_model=JobResponse)
def start_edl_generation(project_id: str, request: Request) -> JobResponse:
    _, _, automation = _services(request)
    return _start_job(
        request,
        project_id,
        "edl",
        lambda context: automation.generate_edl(project_id, context),
        step=4,
    )


@router.get("/projects/{project_id}/edl")
def get_edl(project_id: str, request: Request) -> dict[str, Any]:
    _, _, automation = _services(request)
    result = automation.get_edl(project_id)
    if result is None:
        raise HTTPException(404, "No editing plan exists for this project.")
    return result


@router.put("/projects/{project_id}/edl")
def update_edl(
    project_id: str, payload: EDLUpdateRequest, request: Request
) -> dict[str, Any]:
    _, _, automation = _services(request)
    return automation.update_edl(project_id, payload.model_dump())


@router.post("/projects/{project_id}/edl/validate")
def validate_edl(project_id: str, request: Request) -> dict[str, Any]:
    _, _, automation = _services(request)
    return automation.validate_edl(project_id)


@router.post("/projects/{project_id}/render", response_model=JobResponse)
def start_render(project_id: str, request: Request) -> JobResponse:
    _, _, automation = _services(request)
    return _start_job(
        request,
        project_id,
        "render",
        lambda context: automation.render(project_id, context),
        step=5,
    )


@router.get("/projects/{project_id}/draft")
def get_draft(project_id: str, request: Request) -> dict[str, Any]:
    _, _, automation = _services(request)
    result = automation.draft_details(project_id)
    if result is None:
        raise HTTPException(404, "No rendered draft exists for this project.")
    return result


@router.get("/projects/{project_id}/draft/media")
def get_draft_media(project_id: str, request: Request) -> FileResponse:
    _, _, automation = _services(request)
    path = automation.registered_files(project_id).get("draft")
    if path is None or not path.is_file():
        raise HTTPException(404, "No rendered draft exists for this project.")
    return FileResponse(path, media_type="video/mp4", filename=path.name)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, request: Request) -> JobResponse:
    _, jobs, _ = _services(request)
    return jobs.get(job_id)


@router.post("/jobs/{job_id}/cancel", response_model=JobResponse)
def cancel_job(job_id: str, request: Request) -> JobResponse:
    _, jobs, _ = _services(request)
    return jobs.cancel(job_id)


@router.post("/projects/{project_id}/review")
def submit_review(
    project_id: str, payload: ReviewRequest, request: Request
) -> dict[str, Any]:
    _, _, automation = _services(request)
    return automation.record_review(project_id, **payload.model_dump())


@router.get("/projects/{project_id}/review")
def get_review(project_id: str, request: Request) -> dict[str, Any]:
    _, _, automation = _services(request)
    return automation.review(project_id)


@router.get("/projects/{project_id}/approval", response_model=ApprovalEligibility)
def get_approval(project_id: str, request: Request) -> ApprovalEligibility:
    _, _, automation = _services(request)
    return ApprovalEligibility.model_validate(
        automation.approval_eligibility(project_id)
    )


@router.post("/projects/{project_id}/approve")
def approve(project_id: str, request: Request) -> dict[str, Any]:
    _, _, automation = _services(request)
    return automation.approve(project_id)


@router.get("/projects/{project_id}/evidence", response_model=list[EvidenceItem])
def list_evidence(project_id: str, request: Request) -> list[EvidenceItem]:
    _, _, automation = _services(request)
    return [
        EvidenceItem.model_validate(item)
        for item in automation.evidence_items(project_id)
    ]


@router.get("/projects/{project_id}/evidence/{evidence_id}")
def get_evidence(project_id: str, evidence_id: str, request: Request) -> dict[str, Any]:
    _, _, automation = _services(request)
    try:
        return automation.evidence_payload(project_id, evidence_id)
    except FileNotFoundError as exc:
        raise HTTPException(404, "Evidence file not found.") from exc


@router.get("/projects/{project_id}/files/{file_id}")
def download_file(project_id: str, file_id: str, request: Request) -> FileResponse:
    _, _, automation = _services(request)
    path = automation.registered_files(project_id).get(file_id)
    if path is None or not path.is_file():
        raise HTTPException(404, "Registered project file not found.")
    media_type = "application/json" if path.suffix == ".json" else "video/mp4"
    return FileResponse(path, media_type=media_type, filename=path.name)


def install_exception_handlers(app: Any) -> None:
    @app.exception_handler(ProjectNotFoundError)
    async def project_not_found(_: Request, exc: ProjectNotFoundError) -> Any:
        return _json_error(404, f"Project not found: {exc.args[0]}")

    @app.exception_handler(JobNotFoundError)
    async def job_not_found(_: Request, exc: JobNotFoundError) -> Any:
        return _json_error(404, f"Job not found: {exc.args[0]}")

    from src.errors import PipelineError

    @app.exception_handler(PipelineError)
    async def pipeline_error(_: Request, exc: PipelineError) -> Any:
        return _json_error(422, str(exc))

    @app.exception_handler(ValueError)
    async def value_error(_: Request, exc: ValueError) -> Any:
        return _json_error(422, str(exc))


def _json_error(status_code: int, detail: str) -> Any:
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=status_code, content={"detail": detail})
