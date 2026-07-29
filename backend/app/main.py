"""Local FastAPI application for the guided automation workflow."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import install_exception_handlers, router
from backend.app.services.automation_service import AutomationService
from backend.app.services.job_service import JobService
from backend.app.services.project_service import ProjectService


def create_app(
    *, project_root: Path | None = None, storage_path: Path | None = None
) -> FastAPI:
    root = (project_root or Path.cwd()).resolve()
    project_storage = storage_path or root / "evidence" / "ui" / "projects.json"

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield

    app = FastAPI(
        title="AI-Assisted Multi-Camera Kindergarten Video API",
        description=(
            "Local-only API wrapping the existing deterministic EDL pipeline. "
            "It never approves a draft automatically."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )
    projects = ProjectService(project_storage)
    app.state.project_root = root
    app.state.projects = projects
    app.state.jobs = JobService()
    app.state.automation = AutomationService(root, projects)
    app.include_router(router, prefix="/api")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_exception_handlers(app)
    return app


app = create_app(
    project_root=Path(os.environ.get("KINDERGARTEN_PROJECT_ROOT", Path.cwd()))
)
