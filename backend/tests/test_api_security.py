from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.main import create_app
from backend.app.schemas.api import CameraGroupUpdate
from backend.app.security.path_policy import PathPolicy
from src.errors import InputFileError


def make_client(tmp_path: Path) -> tuple[TestClient, object]:
    (tmp_path / "input").mkdir()
    app = create_app(
        project_root=tmp_path,
        storage_path=tmp_path / "evidence" / "ui" / "projects.json",
    )
    return TestClient(app), app


def test_camera_group_rejects_duplicate_ids() -> None:
    with pytest.raises(ValidationError, match="camera_ids must be unique"):
        CameraGroupUpdate(
            camera_ids=["camera_01", "camera_01"], master_camera="camera_01"
        )


def test_path_policy_rejects_external_and_symlinked_files(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    inside = workspace / "inside.json"
    inside.write_text("{}", encoding="utf-8")
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    link = workspace / "outside-link.json"
    link.symlink_to(outside)
    policy = PathPolicy(workspace)

    assert policy.require_registered_file(inside, {inside}) == inside
    with pytest.raises(InputFileError):
        policy.require_registered_file(outside, {outside})
    with pytest.raises(InputFileError):
        policy.require_registered_file(link, {link})


def test_file_and_evidence_routes_reject_external_registered_paths(
    tmp_path: Path,
) -> None:
    client, app = make_client(tmp_path)
    outside = tmp_path.parent / "outside.json"
    outside.write_text('{"leaked": true}', encoding="utf-8")
    with client:
        project = client.post(
            "/api/projects",
            json={"title": "Boundary Test", "input_folder": "input"},
        ).json()
        app.state.projects.patch(
            project["id"], artifacts={"leaked": str(outside)}
        )

        listed = client.get(f"/api/projects/{project['id']}/evidence")
        download = client.get(f"/api/projects/{project['id']}/files/leaked")
        evidence = client.get(
            f"/api/projects/{project['id']}/evidence/leaked"
        )

    assert listed.status_code == 200
    assert listed.json() == [
        {
            "id": "leaked",
            "label": "Leaked",
            "category": "other",
            "path": "",
            "media_type": "video/mp4",
            "exists": False,
        }
    ]
    assert download.status_code == 404
    assert evidence.status_code == 404
