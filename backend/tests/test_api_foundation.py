from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    (tmp_path / "input").mkdir()
    app = create_app(
        project_root=tmp_path,
        storage_path=tmp_path / "evidence" / "ui" / "projects.json",
    )
    return TestClient(app)


def test_health_and_openapi(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        health = client.get("/api/health")
        docs = client.get("/docs")
        schema = client.get("/openapi.json")
    assert health.status_code == 200
    assert health.json()["local_only"] is True
    assert docs.status_code == 200
    assert schema.status_code == 200
    paths = schema.json()["paths"]
    expected = {
        "/api/projects",
        "/api/projects/{project_id}/analysis",
        "/api/projects/{project_id}/sync/detect",
        "/api/projects/{project_id}/sync/confirm",
        "/api/projects/{project_id}/edl/generate",
        "/api/projects/{project_id}/edl/validate",
        "/api/projects/{project_id}/render",
        "/api/projects/{project_id}/draft/media",
        "/api/jobs/{job_id}",
        "/api/projects/{project_id}/review",
        "/api/projects/{project_id}/approve",
        "/api/projects/{project_id}/evidence",
    }
    assert expected <= set(paths)


def test_project_crud_persists_state(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        created = client.post(
            "/api/projects",
            json={
                "title": "Graduation Demo",
                "input_folder": "input",
                "duration_seconds": 90,
            },
        )
        assert created.status_code == 201
        project_id = created.json()["id"]
        updated = client.put(
            f"/api/projects/{project_id}",
            json={"duration_seconds": 72, "smoke_mode": False},
        )
        fetched = client.get(f"/api/projects/{project_id}")
        deleted = client.delete(f"/api/projects/{project_id}")
        missing = client.get(f"/api/projects/{project_id}")
    assert updated.json()["duration_seconds"] == 72
    assert fetched.json()["title"] == "Graduation Demo"
    assert deleted.status_code == 204
    assert missing.status_code == 404


def test_project_rejects_path_outside_workspace(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.post(
            "/api/projects",
            json={
                "title": "Unsafe",
                "input_folder": str(tmp_path.parent),
                "duration_seconds": 90,
            },
        )
    assert response.status_code == 422


def test_analysis_job_fails_truthfully_for_empty_input(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        project = client.post(
            "/api/projects",
            json={"title": "Empty", "input_folder": "input"},
        ).json()
        started = client.post(f"/api/projects/{project['id']}/analysis")
        assert started.status_code == 200
        job_id = started.json()["job_id"]
        terminal = None
        for _ in range(100):
            terminal = client.get(f"/api/jobs/{job_id}").json()
            if terminal["status"] in {"COMPLETED", "FAILED"}:
                break
        analysis = client.get(f"/api/projects/{project['id']}/analysis")
    assert terminal is not None
    assert terminal["status"] == "COMPLETED"
    assert terminal["result"]["outcome"] == "NEEDS_CAMERA_SELECTION"
    assert terminal["result"]["discovered_videos"] == 0
    assert analysis.status_code == 200
    assert {
        "common_overlap_duration",
        "total_event_coverage",
        "maximum_renderable_duration",
    } <= set(analysis.json())
