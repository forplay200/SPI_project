from __future__ import annotations

import threading

from backend.app.schemas.api import JobStatus
from backend.app.services.job_service import JobService


class _PauseAfterCancellationCheck(JobService):
    def __init__(self) -> None:
        super().__init__(max_workers=1)
        self.checked_after_handler = threading.Event()
        self.release_check = threading.Event()
        self._uncancelled_checks = 0

    def is_cancelled(self, job_id: str) -> bool:
        cancelled = super().is_cancelled(job_id)
        if not cancelled:
            self._uncancelled_checks += 1
            if self._uncancelled_checks == 2:
                self.checked_after_handler.set()
                if not self.release_check.wait(timeout=2):
                    raise AssertionError("timed out waiting for cancellation")
        return cancelled


def test_cancellation_cannot_be_overwritten_by_late_completion() -> None:
    service = _PauseAfterCancellationCheck()
    try:
        started = service.start(
            "project-1", "analysis", lambda _: {"ok": True}, step=1
        )
        assert service.checked_after_handler.wait(timeout=2)

        cancelled = service.cancel(started.job_id)
        assert cancelled.status is JobStatus.CANCELLED

        service.release_check.set()
        service._executor.shutdown(wait=True)

        assert service.get(started.job_id).status is JobStatus.CANCELLED
    finally:
        service.release_check.set()
        service._executor.shutdown(wait=True)
