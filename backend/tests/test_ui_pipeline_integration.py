from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from src.preflight import check_dependencies


def _wait(
    client: TestClient, job_id: str, *, timeout: float = 240
) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == 200
        job = response.json()
        if job["status"] in {"COMPLETED", "FAILED", "CANCELLED"}:
            return job
        time.sleep(0.1)
    raise AssertionError(f"Timed out waiting for {job_id}")


@pytest.mark.skipif(
    os.environ.get("PIPELINE_UI_INTEGRATION") != "1",
    reason="Set PIPELINE_UI_INTEGRATION=1 for the approved-footage UI API workflow.",
)
def test_api_guided_smoke_workflow_never_approves(tmp_path: Path) -> None:
    root = Path.cwd().resolve()
    dependencies = check_dependencies("moviepy", allow_ffmpeg_fallback=True)
    if not dependencies.selected_renderer_ready:
        pytest.skip("MoviePy/FFmpeg/FFprobe are unavailable for UI integration.")
    app = create_app(
        project_root=root,
        storage_path=tmp_path / "projects.json",
    )
    with TestClient(app) as client:
        created = client.post(
            "/api/projects",
            json={
                "title": "Guided UI Integration",
                "input_folder": "input",
                "duration_seconds": 18,
                "smoke_mode": True,
                "credits": "Edited by the Project Team",
            },
        )
        assert created.status_code == 201
        project_id = created.json()["id"]

        analysis = _wait(
            client,
            client.post(f"/api/projects/{project_id}/analysis").json()["job_id"],
        )
        assert analysis["status"] == "COMPLETED", analysis
        assert analysis["result"]["selected_camera_ids"]

        sync = _wait(
            client,
            client.post(f"/api/projects/{project_id}/sync/detect").json()["job_id"],
        )
        assert sync["status"] == "COMPLETED", sync
        assert sync["result"]["acceptance_status"] == "needs_human_confirmation"
        assert {
            "common_overlap_duration",
            "total_event_coverage",
            "maximum_renderable_duration",
        } <= set(sync["result"]["duration_metrics"])

        edl = _wait(
            client,
            client.post(f"/api/projects/{project_id}/edl/generate").json()["job_id"],
        )
        assert edl["status"] == "COMPLETED", edl
        assert edl["result"]["validation"]["valid"] is True

        render = _wait(
            client,
            client.post(f"/api/projects/{project_id}/render").json()["job_id"],
        )
        assert render["status"] == "COMPLETED", render
        draft = client.get(f"/api/projects/{project_id}/draft").json()
        assert "smoke" in draft["filename"]
        assert draft["metadata"]["has_video"] is True
        assert draft["metadata"]["has_audio"] is True
        assert draft["maximum_renderable_duration"] >= 18

        eligibility = client.get(f"/api/projects/{project_id}/approval").json()
        assert eligibility["eligible"] is False
        approval = client.post(f"/api/projects/{project_id}/approve")
        assert approval.status_code == 422
        assert client.get(f"/api/projects/{project_id}/evidence").json()
