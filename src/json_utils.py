"""Small JSON helpers with consistent errors and atomic writes."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .errors import ConfigurationError


def read_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except FileNotFoundError as exc:
        raise ConfigurationError(f"{label} file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"{label} is not valid JSON at line {exc.lineno}, column {exc.colno}: {path}"
        ) from exc
    except OSError as exc:
        raise ConfigurationError(f"Cannot read {label} file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ConfigurationError(f"{label} root must be a JSON object: {path}")
    return value


def write_json_atomic(path: Path, value: object) -> None:
    """Write JSON in the destination directory and atomically replace the target."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.stem}-", suffix=".tmp"
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def write_generated_json(path: Path, value: object, *, overwrite: bool = False) -> None:
    """Write a generated JSON file without replacing different existing content."""
    normalized_value = json.loads(json.dumps(value, ensure_ascii=False))
    if path.exists() and not overwrite:
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigurationError(
                f"Generated destination already exists and cannot be compared: {path}. "
                "Use --overwrite only after reviewing it."
            ) from exc
        if existing == normalized_value:
            return
        raise ConfigurationError(
            f"Generated destination already contains different data: {path}. "
            "Review it and rerun with --overwrite to replace it."
        )
    write_json_atomic(path, value)
