"""Dependency and executable checks performed before expensive work."""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from .errors import PreflightError


@dataclass(frozen=True)
class PreflightReport:
    moviepy_available: bool
    ffmpeg_path: str | None
    ffprobe_path: str | None
    selected_renderer_ready: bool
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def resolve_executable(name: str, explicit_path: Path | None = None) -> str | None:
    """Return a verified executable path without invoking a shell."""
    if explicit_path is not None:
        candidate = explicit_path.resolve()
        return str(candidate) if candidate.is_file() else None
    system_path = shutil.which(name)
    if system_path:
        return system_path
    executable_name = f"{name}.exe" if os.name == "nt" else name
    local_temp = Path.cwd() / "temp"
    if local_temp.is_dir():
        candidates = sorted(
            (
                path
                for path in local_temp.rglob(executable_name)
                if path.is_file() and path.parent.name.casefold() == "bin"
            ),
            key=lambda path: path.as_posix().casefold(),
        )
        if candidates:
            return str(candidates[0].resolve())
    return None


def _works(executable: str | None, version_flag: str = "-version") -> bool:
    if not executable:
        return False
    try:
        completed = subprocess.run(
            [executable, version_flag],
            check=False,
            capture_output=True,
            text=True,
            shell=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0


def check_dependencies(
    renderer: str,
    *,
    allow_ffmpeg_fallback: bool = True,
    ffmpeg_path: Path | None = None,
    ffprobe_path: Path | None = None,
) -> PreflightReport:
    """Check renderer dependencies and return all non-fatal warnings."""
    moviepy_available = importlib.util.find_spec("moviepy") is not None
    ffmpeg = resolve_executable("ffmpeg", ffmpeg_path)
    ffprobe = resolve_executable("ffprobe", ffprobe_path)
    ffmpeg_ok = _works(ffmpeg)
    ffprobe_ok = _works(ffprobe)
    warnings: list[str] = []
    if not ffprobe_ok:
        warnings.append(
            "FFprobe is unavailable; media validation and output evidence cannot run."
        )
    if not ffmpeg_ok:
        warnings.append("FFmpeg is unavailable; fallback rendering cannot run.")
    if not moviepy_available:
        warnings.append("MoviePy is unavailable; the primary renderer cannot run.")

    selected_ready = (renderer == "moviepy" and moviepy_available and ffprobe_ok) or (
        renderer == "ffmpeg" and ffmpeg_ok and ffprobe_ok
    )
    if renderer == "moviepy" and not moviepy_available and allow_ffmpeg_fallback:
        selected_ready = ffmpeg_ok and ffprobe_ok
    return PreflightReport(
        moviepy_available=moviepy_available,
        ffmpeg_path=ffmpeg if ffmpeg_ok else None,
        ffprobe_path=ffprobe if ffprobe_ok else None,
        selected_renderer_ready=selected_ready,
        warnings=tuple(warnings),
    )


def require_dependencies(report: PreflightReport) -> None:
    if not report.selected_renderer_ready:
        details = (
            " ".join(report.warnings)
            or "Required renderer dependencies are unavailable."
        )
        raise PreflightError(
            f"Renderer preflight failed. {details} Install requirements and FFmpeg/FFprobe, "
            "then run the preflight command again."
        )
