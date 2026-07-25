"""Renderer-neutral master-to-source timeline mapping."""

from __future__ import annotations

from .errors import RenderPlanError
from .models import EDL, ProjectConfig, RenderInstruction, RenderPlan


def build_render_plan(config: ProjectConfig, edl: EDL) -> RenderPlan:
    cameras = {camera.id: camera for camera in config.cameras}
    instructions: list[RenderInstruction] = []
    errors: list[str] = []
    for segment in edl.timeline:
        camera = cameras.get(segment.camera)
        if camera is None:
            errors.append(
                f"Segment {segment.id!r} references unknown camera {segment.camera!r}."
            )
            continue
        source_start = round(segment.start + camera.offset_seconds, 6)
        source_end = round(segment.end + camera.offset_seconds, 6)
        if source_start < 0:
            errors.append(
                f"Segment {segment.id!r} maps to negative source start "
                f"{source_start:.3f}s for camera {camera.id!r}."
            )
        if camera.duration_seconds is None:
            errors.append(
                f"Camera {camera.id!r} has no probed duration; probe media before planning."
            )
        elif source_end > camera.duration_seconds + 0.001:
            errors.append(
                f"Segment {segment.id!r} source end {source_end:.3f}s exceeds "
                f"camera {camera.id!r} duration {camera.duration_seconds:.3f}s."
            )
        instructions.append(
            RenderInstruction(
                segment_id=segment.id,
                source_path=camera.path,
                master_start=segment.start,
                master_end=segment.end,
                source_start=source_start,
                source_end=source_end,
                camera_id=camera.id,
                action=segment.action,
                reason=segment.reason,
                overlay=segment.overlay,
                has_audio=bool(camera.has_audio),
            )
        )
    if errors:
        raise RenderPlanError("Render-plan errors:\n- " + "\n- ".join(errors))
    expected_duration = (
        sum(instruction.duration for instruction in instructions)
        + config.title.duration
        + config.credits.duration
    )
    return RenderPlan(
        project=config.project,
        title=config.title,
        credits=config.credits,
        output=config.output,
        duration_policy=config.duration_policy,
        instructions=tuple(instructions),
        expected_duration_seconds=expected_duration,
        renderer=config.renderer,
        allow_ffmpeg_fallback=config.allow_ffmpeg_fallback,
        camera_offsets={camera.id: camera.offset_seconds for camera in config.cameras},
    )


def format_render_plan(plan: RenderPlan) -> str:
    lines = [
        f"Project: {plan.project}",
        f"Renderer: {plan.renderer}",
        f"Output: {plan.output.width}x{plan.output.height} at {plan.output.fps} fps",
        f"Expected final duration: {plan.expected_duration_seconds:.3f}s",
        f"Camera switches: {plan.switch_count}",
        "Segments:",
    ]
    lines.extend(
        "  "
        f"{item.segment_id}: master {item.master_start:.3f}–{item.master_end:.3f}s "
        f"=> {item.camera_id} {item.source_start:.3f}–{item.source_end:.3f}s "
        f"[{item.action}] — {item.reason}"
        for item in plan.instructions
    )
    return "\n".join(lines)
