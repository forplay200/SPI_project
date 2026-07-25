"""Stable renderer interface and backend selection."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .errors import MoviePyRenderError
from .models import RenderPlan, RenderResult


class Renderer(Protocol):
    def render(self, plan: RenderPlan, output_path: Path) -> RenderResult:
        """Render the immutable plan to a temporary MP4 path."""


def render_with_selected_backend(
    plan: RenderPlan,
    output_path: Path,
    *,
    ffmpeg_executable: str | Path | None = None,
    command_log_path: Path | None = None,
) -> RenderResult:
    """Render with the selected backend and a visible, controlled fallback."""
    if plan.renderer == "ffmpeg":
        from .ffmpeg_renderer import FFmpegRenderer

        return FFmpegRenderer(
            ffmpeg_executable=ffmpeg_executable,
            command_log_path=command_log_path,
        ).render(plan, output_path)

    from .moviepy_renderer import MoviePyRenderer

    try:
        return MoviePyRenderer().render(plan, output_path)
    except MoviePyRenderError as exc:
        if not plan.allow_ffmpeg_fallback:
            raise
        from .ffmpeg_renderer import FFmpegRenderer

        fallback = FFmpegRenderer(
            ffmpeg_executable=ffmpeg_executable,
            command_log_path=command_log_path,
        ).render(plan, output_path)
        return RenderResult(
            output_path=fallback.output_path,
            backend=fallback.backend,
            started_at=fallback.started_at,
            completed_at=fallback.completed_at,
            duration_seconds=fallback.duration_seconds,
            warnings=(f"FFmpeg fallback activated after MoviePy failure: {exc}",)
            + fallback.warnings,
            command_log_path=fallback.command_log_path,
            fallback_reason=str(exc),
        )
