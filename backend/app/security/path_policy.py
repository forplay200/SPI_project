"""Restrict browser-supplied paths to this local project workspace."""

from __future__ import annotations

from pathlib import Path

from src.errors import InputFileError


class PathPolicy:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()

    def resolve_input_directory(self, value: str | Path) -> Path:
        raw = Path(value)
        resolved = (raw if raw.is_absolute() else self.project_root / raw).resolve()
        if not self._within(resolved, self.project_root):
            raise InputFileError(
                "The input folder must be inside the local project workspace."
            )
        if not resolved.is_dir():
            raise InputFileError(f"Input folder does not exist: {value}")
        return resolved

    def require_registered_file(self, value: str | Path, registered: set[Path]) -> Path:
        resolved = Path(value).resolve()
        allowed = {path.resolve() for path in registered}
        if resolved not in allowed or not resolved.is_file():
            raise InputFileError(
                "The requested local file is not registered for this project."
            )
        return resolved

    @staticmethod
    def _within(path: Path, parent: Path) -> bool:
        try:
            path.relative_to(parent)
            return True
        except ValueError:
            return False
