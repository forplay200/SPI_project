"""Small persistent local project store for the guided UI."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any
from uuid import uuid4

from backend.app.schemas.api import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    utc_now,
)
from src.json_utils import write_json_atomic


class ProjectNotFoundError(KeyError):
    pass


class ProjectService:
    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self._lock = threading.RLock()
        self._records: dict[str, dict[str, Any]] = {}
        self._runtime: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if not self.storage_path.is_file():
            return
        try:
            value = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(value, dict):
            self._records = {
                key: item
                for key, item in value.items()
                if isinstance(key, str) and isinstance(item, dict)
            }

    def _save(self) -> None:
        write_json_atomic(self.storage_path, self._records)

    def create(self, data: ProjectCreate) -> ProjectResponse:
        with self._lock:
            project_id = f"project-{uuid4().hex[:12]}"
            now = utc_now()
            record = {
                **data.model_dump(),
                "id": project_id,
                "created_at": now,
                "updated_at": now,
                "outcome": "INVALID_INPUT",
                "current_step": 1,
                "artifacts": {},
                "latest_job_id": None,
            }
            self._records[project_id] = record
            self._save()
            return ProjectResponse.model_validate(record)

    def get(self, project_id: str) -> ProjectResponse:
        with self._lock:
            try:
                record = self._records[project_id]
            except KeyError as exc:
                raise ProjectNotFoundError(project_id) from exc
            return ProjectResponse.model_validate(record)

    def update(self, project_id: str, data: ProjectUpdate) -> ProjectResponse:
        changes = data.model_dump(exclude_unset=True)
        return self.patch(project_id, **changes)

    def patch(self, project_id: str, **changes: Any) -> ProjectResponse:
        with self._lock:
            if project_id not in self._records:
                raise ProjectNotFoundError(project_id)
            record = self._records[project_id]
            record.update(changes)
            record["updated_at"] = utc_now()
            self._save()
            return ProjectResponse.model_validate(record)

    def delete(self, project_id: str) -> None:
        with self._lock:
            if project_id not in self._records:
                raise ProjectNotFoundError(project_id)
            del self._records[project_id]
            self._runtime.pop(project_id, None)
            self._save()

    def set_runtime(self, project_id: str, key: str, value: Any) -> None:
        self.get(project_id)
        with self._lock:
            self._runtime.setdefault(project_id, {})[key] = value

    def runtime(self, project_id: str, key: str, default: Any = None) -> Any:
        self.get(project_id)
        with self._lock:
            return self._runtime.get(project_id, {}).get(key, default)
