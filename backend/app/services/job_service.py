"""In-process background jobs with meaningful pipeline stage updates."""

from __future__ import annotations

import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from typing import Any
from uuid import uuid4

from backend.app.schemas.api import TERMINAL_JOB_STATES, JobResponse, JobStatus, utc_now


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    project_id: str
    operation: str
    status: JobStatus
    progress: int
    message: str
    current_step: int
    warning: str | None
    error: str | None
    result: dict[str, Any] | None
    created_at: str
    updated_at: str


class JobNotFoundError(KeyError):
    pass


class JobContext:
    def __init__(self, service: JobService, job_id: str) -> None:
        self.service = service
        self.job_id = job_id

    def update(
        self, status: JobStatus, progress: int, message: str, *, current_step: int
    ) -> None:
        self.service._update(
            self.job_id,
            status=status,
            progress=progress,
            message=message,
            current_step=current_step,
        )
        if self.service.is_cancelled(self.job_id):
            raise JobCancelledError("Job cancelled by the user.")


class JobCancelledError(RuntimeError):
    pass


JobHandler = Callable[[JobContext], dict[str, Any]]


class JobService:
    def __init__(self, *, max_workers: int = 2) -> None:
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="local-video-job"
        )
        self._jobs: dict[str, JobRecord] = {}
        self._cancelled: set[str] = set()

    def start(
        self, project_id: str, operation: str, handler: JobHandler, *, step: int
    ) -> JobResponse:
        job_id = f"job-{uuid4().hex[:12]}"
        now = utc_now()
        record = JobRecord(
            job_id=job_id,
            project_id=project_id,
            operation=operation,
            status=JobStatus.QUEUED,
            progress=0,
            message="Waiting for local processing",
            current_step=step,
            warning=None,
            error=None,
            result=None,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._jobs[job_id] = record
        self._executor.submit(self._run, job_id, handler)
        return self._response(record)

    def _run(self, job_id: str, handler: JobHandler) -> None:
        try:
            if self.is_cancelled(job_id):
                raise JobCancelledError("Job cancelled before it started.")
            result = handler(JobContext(self, job_id))
            if self.is_cancelled(job_id):
                raise JobCancelledError("Job cancelled at a safe stage boundary.")
            self._update(
                job_id,
                status=JobStatus.COMPLETED,
                progress=100,
                message="Completed",
                result=result,
            )
        except JobCancelledError as exc:
            self._update(
                job_id,
                status=JobStatus.CANCELLED,
                message=str(exc),
                warning=str(exc),
            )
        except Exception as exc:  # noqa: BLE001 - terminal job boundary records failures
            self._update(
                job_id,
                status=JobStatus.FAILED,
                message="Local processing failed",
                error=str(exc),
            )

    def _update(self, job_id: str, **changes: Any) -> None:
        with self._lock:
            record = self._jobs[job_id]
            if record.status in TERMINAL_JOB_STATES:
                return
            self._jobs[job_id] = replace(record, updated_at=utc_now(), **changes)

    def get(self, job_id: str) -> JobResponse:
        with self._lock:
            try:
                return self._response(self._jobs[job_id])
            except KeyError as exc:
                raise JobNotFoundError(job_id) from exc

    def cancel(self, job_id: str) -> JobResponse:
        with self._lock:
            if job_id not in self._jobs:
                raise JobNotFoundError(job_id)
            if self._jobs[job_id].status not in TERMINAL_JOB_STATES:
                self._cancelled.add(job_id)
                self._update(
                    job_id,
                    status=JobStatus.CANCELLED,
                    message="Cancellation requested",
                    warning="Cancellation takes effect at the next safe stage boundary.",
                )
            return self._response(self._jobs[job_id])

    def is_cancelled(self, job_id: str) -> bool:
        with self._lock:
            return job_id in self._cancelled

    @staticmethod
    def _response(record: JobRecord) -> JobResponse:
        return JobResponse.model_validate(record.__dict__)
