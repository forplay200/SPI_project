"""Direct FFmpeg fallback renderer with reproducible command evidence."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic

from .errors import FFmpegRenderError
from .models import RenderInstruction, RenderPlan, RenderResult
from .preflight import resolve_executable


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def escape_drawtext(text: str) -> str:
    """Escape values used inside a single-quoted FFmpeg drawtext expression."""
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", r"\'")
        .replace("%", r"\%")
        .replace("\n", r"\n")
    )


def _transition_filter(instruction: RenderInstruction) -> str:
    transition_duration = min(1.0, instruction.duration / 2)
    if instruction.action == "fade_in":
        return f",fade=t=in:st=0:d={transition_duration:.6f}"
    if instruction.action in {"fade_out", "fade_to_black"}:
        start = max(0.0, instruction.duration - transition_duration)
        return f",fade=t=out:st={start:.6f}:d={transition_duration:.6f}"
    return ""


def build_ffmpeg_command(
    plan: RenderPlan,
    output_path: Path,
    *,
    ffmpeg_executable: str,
) -> tuple[list[str], str]:
    """Build an argument-array command and its filter graph from validated values."""
    command = [ffmpeg_executable, "-hide_banner", "-y"]
    for instruction in plan.instructions:
        command.extend(
            [
                "-ss",
                f"{instruction.source_start:.6f}",
                "-t",
                f"{instruction.duration:.6f}",
                "-i",
                str(instruction.source_path),
            ]
        )
    width, height, fps = plan.output.width, plan.output.height, plan.output.fps
    filters: list[str] = []
    filters.append(
        f"color=c=black:s={width}x{height}:r={fps}:d={plan.title.duration:.6f},"
        f"drawtext=text='{escape_drawtext(plan.title.text)}':fontcolor=white:"
        f"fontsize={max(28, height // 14)}:x=(w-text_w)/2:y=(h-text_h)/2,"
        "format=yuv420p[v0]"
    )
    filters.append(
        f"anullsrc=channel_layout=stereo:sample_rate=48000:d={plan.title.duration:.6f}[a0]"
    )
    for index, instruction in enumerate(plan.instructions, start=1):
        video_filter = (
            f"[{index - 1}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
            f"fps={fps},setsar=1,setpts=PTS-STARTPTS"
        )
        video_filter += _transition_filter(instruction)
        if instruction.overlay is not None:
            overlay = instruction.overlay
            absolute_start = (
                instruction.master_start if overlay.start is None else overlay.start
            )
            absolute_end = (
                instruction.master_end if overlay.end is None else overlay.end
            )
            local_start = absolute_start - instruction.master_start
            local_end = absolute_end - instruction.master_start
            y = {
                "top": "h*0.08",
                "center": "(h-text_h)/2",
                "bottom": "h-text_h-h*0.08",
            }.get(overlay.position or "bottom", "h-text_h-h*0.08")
            box_y = {
                "top": int(height * 0.04),
                "center": int(height * 0.40),
                "bottom": int(height * 0.78),
            }.get(overlay.position or "bottom", int(height * 0.78))
            box_x = int(width * 0.08)
            box_width = int(width * 0.84)
            video_filter += (
                f",drawbox=x={box_x}:y={box_y}:w={box_width}:"
                f"h={max(40, height // 8)}:"
                f"color=black@0.70:t=fill:enable='between(t,{local_start:.6f},{local_end:.6f})'"
                f",drawtext=text='{escape_drawtext(overlay.text)}':fontcolor=white:"
                f"fontsize={max(24, height // 25)}:x=(w-text_w)/2:y={y}:"
                f"enable='between(t,{local_start:.6f},{local_end:.6f})'"
            )
        filters.append(f"{video_filter}[v{index}]")
        audio_fade = ""
        transition_duration = min(1.0, instruction.duration / 2)
        if instruction.action == "fade_in":
            audio_fade = f",afade=t=in:st=0:d={transition_duration:.6f}"
        elif instruction.action in {"fade_out", "fade_to_black"}:
            audio_fade = (
                f",afade=t=out:st={instruction.duration - transition_duration:.6f}:"
                f"d={transition_duration:.6f}"
            )
        if instruction.has_audio:
            filters.append(
                f"[{index - 1}:a]aresample=48000,asetpts=PTS-STARTPTS"
                f"{audio_fade}[a{index}]"
            )
        else:
            filters.append(
                f"anullsrc=channel_layout=stereo:sample_rate=48000:"
                f"d={instruction.duration:.6f}{audio_fade}[a{index}]"
            )
    credit_index = len(plan.instructions) + 1
    filters.append(
        f"color=c=black:s={width}x{height}:r={fps}:d={plan.credits.duration:.6f},"
        f"drawtext=text='{escape_drawtext(plan.credits.text)}':fontcolor=white:"
        f"fontsize={max(28, height // 14)}:x=(w-text_w)/2:y=(h-text_h)/2,"
        f"format=yuv420p[v{credit_index}]"
    )
    filters.append(
        f"anullsrc=channel_layout=stereo:sample_rate=48000:"
        f"d={plan.credits.duration:.6f}[a{credit_index}]"
    )
    concat_inputs = "".join(f"[v{i}][a{i}]" for i in range(credit_index + 1))
    filters.append(f"{concat_inputs}concat=n={credit_index + 1}:v=1:a=1[vout][aout]")
    filter_graph = ";\n".join(filters)
    command.extend(
        [
            "-filter_complex",
            filter_graph,
            "-map",
            "[vout]",
            "-map",
            "[aout]",
            "-c:v",
            plan.output.video_codec,
            "-c:a",
            plan.output.audio_codec,
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-shortest",
            str(output_path),
        ]
    )
    return command, filter_graph


class FFmpegRenderer:
    backend = "ffmpeg"

    def __init__(
        self,
        *,
        ffmpeg_executable: str | Path | None = None,
        command_log_path: Path | None = None,
    ) -> None:
        self.ffmpeg_executable = (
            str(ffmpeg_executable)
            if ffmpeg_executable is not None
            else resolve_executable("ffmpeg")
        )
        self.command_log_path = command_log_path

    def render(self, plan: RenderPlan, output_path: Path) -> RenderResult:
        if not self.ffmpeg_executable:
            raise FFmpegRenderError(
                "FFmpeg executable was not found. Install FFmpeg or select a working path."
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command, filter_graph = build_ffmpeg_command(
            plan, output_path, ffmpeg_executable=self.ffmpeg_executable
        )
        started_at = _utc_now()
        timer = monotonic()
        log_path = self.command_log_path
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                shell=False,
                timeout=max(120, int(plan.expected_duration_seconds * 10)),
            )
        except (OSError, subprocess.SubprocessError) as exc:
            if log_path is not None:
                log_path.write_text(
                    json.dumps(
                        {
                            "command": command,
                            "filter_graph": filter_graph,
                            "exception": str(exc),
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
            raise FFmpegRenderError(f"Could not execute FFmpeg: {exc}") from exc
        elapsed = monotonic() - timer
        if log_path is not None:
            log_path.write_text(
                json.dumps(
                    {
                        "command": command,
                        "filter_graph": filter_graph,
                        "return_code": completed.returncode,
                        "stdout": completed.stdout,
                        "stderr": completed.stderr,
                        "elapsed_seconds": elapsed,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        if completed.returncode != 0:
            detail = completed.stderr.strip()[-2000:]
            raise FFmpegRenderError(
                f"FFmpeg failed with exit code {completed.returncode}: {detail}"
            )
        if not output_path.is_file() or output_path.stat().st_size == 0:
            raise FFmpegRenderError(
                "FFmpeg reported success but did not create a non-empty MP4."
            )
        return RenderResult(
            output_path=output_path,
            backend=self.backend,
            started_at=started_at,
            completed_at=_utc_now(),
            duration_seconds=elapsed,
            command_log_path=log_path,
        )
