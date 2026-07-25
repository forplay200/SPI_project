"""MoviePy draft renderer with Pillow-generated local text assets."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from typing import Any

from .errors import MoviePyRenderError
from .models import OverlaySpec, RenderPlan, RenderResult

LOGGER = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _call(clip: Any, modern: str, legacy: str, *args: Any, **kwargs: Any) -> Any:
    method = getattr(clip, modern, None) or getattr(clip, legacy, None)
    if method is None:
        raise MoviePyRenderError(f"Installed MoviePy lacks {modern}/{legacy}.")
    return method(*args, **kwargs)


def _silent_audio(
    AudioArrayClip: Any, np: Any, duration: float, fps: int = 44100
) -> Any:
    samples = max(1, round(duration * fps))
    return AudioArrayClip(np.zeros((samples, 2), dtype=float), fps=fps)


def _text_image(
    np: Any,
    *,
    text: str,
    size: tuple[int, int],
    font_size: int,
    lower_third: bool = False,
) -> Any:
    from PIL import Image, ImageDraw, ImageFont

    width, height = size
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.load_default(size=font_size)
        except TypeError:
            font = ImageFont.load_default()
    max_text_width = int(width * 0.86)
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        box = draw.textbbox((0, 0), candidate, font=font)
        if current and box[2] - box[0] > max_text_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    display = "\n".join(lines) or text
    box = draw.multiline_textbbox((0, 0), display, font=font, spacing=8, align="center")
    text_width, text_height = box[2] - box[0], box[3] - box[1]
    x = (width - text_width) / 2
    y = (height - text_height) / 2
    if lower_third:
        padding = max(12, font_size // 3)
        draw.rounded_rectangle(
            (
                max(20, x - padding),
                max(0, y - padding),
                min(width - 20, x + text_width + padding),
                min(height, y + text_height + padding),
            ),
            radius=12,
            fill=(0, 0, 0, 190),
        )
    draw.multiline_text(
        (x, y),
        display,
        font=font,
        fill=(255, 255, 255, 255),
        spacing=8,
        align="center",
        stroke_width=2,
        stroke_fill=(0, 0, 0, 255),
    )
    return np.array(image)


class MoviePyRenderer:
    """Primary renderer. Imports MoviePy only when rendering is requested."""

    backend = "moviepy"

    def render(self, plan: RenderPlan, output_path: Path) -> RenderResult:
        started_at = _utc_now()
        timer = monotonic()
        resources: list[Any] = []
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            try:
                import numpy as np

                try:
                    from moviepy import (
                        AudioArrayClip,
                        ColorClip,
                        CompositeVideoClip,
                        ImageClip,
                        VideoFileClip,
                        afx,
                        concatenate_videoclips,
                        vfx,
                    )
                except ImportError:
                    from moviepy.audio.AudioClip import AudioArrayClip
                    from moviepy.editor import (  # type: ignore[no-redef]
                        ColorClip,
                        CompositeVideoClip,
                        ImageClip,
                        VideoFileClip,
                        afx,
                        concatenate_videoclips,
                        vfx,
                    )
            except ImportError as exc:
                raise MoviePyRenderError(
                    "MoviePy and Pillow are required for the primary renderer."
                ) from exc

            size = (plan.output.width, plan.output.height)

            def attach_silence(clip: Any, duration: float) -> Any:
                audio = _silent_audio(AudioArrayClip, np, duration)
                resources.append(audio)
                result = _call(clip, "with_audio", "set_audio", audio)
                resources.append(result)
                return result

            def text_screen(text: str, duration: float) -> Any:
                background = _call(
                    ColorClip(size=size, color=(0, 0, 0)),
                    "with_duration",
                    "set_duration",
                    duration,
                )
                resources.append(background)
                image = ImageClip(
                    _text_image(
                        np,
                        text=text,
                        size=size,
                        font_size=max(28, plan.output.height // 14),
                    )
                )
                image = _call(image, "with_duration", "set_duration", duration)
                resources.append(image)
                composite = CompositeVideoClip([background, image], size=size)
                resources.append(composite)
                return attach_silence(composite, duration)

            clips: list[Any] = [text_screen(plan.title.text, plan.title.duration)]
            for instruction in plan.instructions:
                source = VideoFileClip(str(instruction.source_path))
                resources.append(source)
                clip = _call(
                    source,
                    "subclipped",
                    "subclip",
                    instruction.source_start,
                    instruction.source_end,
                )
                resources.append(clip)
                scale = min(size[0] / clip.w, size[1] / clip.h)
                resized = _call(
                    clip,
                    "resized",
                    "resize",
                    new_size=(
                        max(1, round(clip.w * scale)),
                        max(1, round(clip.h * scale)),
                    ),
                )
                resources.append(resized)
                background = _call(
                    ColorClip(size=size, color=(0, 0, 0)),
                    "with_duration",
                    "set_duration",
                    instruction.duration,
                )
                resources.append(background)
                positioned = _call(resized, "with_position", "set_position", "center")
                resources.append(positioned)
                normalized = CompositeVideoClip([background, positioned], size=size)
                resources.append(normalized)
                if resized.audio is not None:
                    normalized = _call(
                        normalized, "with_audio", "set_audio", resized.audio
                    )
                    resources.append(normalized)
                else:
                    normalized = attach_silence(normalized, instruction.duration)
                normalized = _call(normalized, "with_fps", "set_fps", plan.output.fps)
                resources.append(normalized)
                normalized = self._apply_transition(
                    normalized, instruction.action, instruction.duration, vfx, afx
                )
                resources.append(normalized)
                if instruction.overlay is not None:
                    normalized = self._apply_overlay(
                        normalized,
                        instruction.overlay,
                        instruction.master_start,
                        instruction.master_end,
                        size,
                        ImageClip,
                        CompositeVideoClip,
                        np,
                    )
                    resources.append(normalized)
                clips.append(normalized)
            clips.append(text_screen(plan.credits.text, plan.credits.duration))
            final = concatenate_videoclips(clips, method="compose")
            resources.append(final)
            try:
                final.write_videofile(
                    str(output_path),
                    fps=plan.output.fps,
                    codec=plan.output.video_codec,
                    audio_codec=plan.output.audio_codec,
                    temp_audiofile=str(output_path.with_suffix(".audio.m4a")),
                    remove_temp=True,
                    logger=None,
                )
            except Exception as exc:
                raise MoviePyRenderError(f"MoviePy export failed: {exc}") from exc
        except MoviePyRenderError:
            raise
        except Exception as exc:
            raise MoviePyRenderError(f"MoviePy rendering failed: {exc}") from exc
        finally:
            seen: set[int] = set()
            for resource in reversed(resources):
                if id(resource) in seen:
                    continue
                seen.add(id(resource))
                try:
                    resource.close()
                except Exception as close_error:  # noqa: BLE001
                    LOGGER.warning(
                        "Could not close a MoviePy resource: %s", close_error
                    )
        return RenderResult(
            output_path=output_path,
            backend=self.backend,
            started_at=started_at,
            completed_at=_utc_now(),
            duration_seconds=monotonic() - timer,
        )

    @staticmethod
    def _apply_transition(
        clip: Any, action: str, duration: float, vfx: Any, afx: Any
    ) -> Any:
        transition_duration = min(1.0, duration / 2)
        if action == "cut":
            return clip
        fade_in = action == "fade_in"
        try:
            effect_class = vfx.FadeIn if fade_in else vfx.FadeOut
            result = clip.with_effects([effect_class(transition_duration)])
            if result.audio is not None:
                audio_effect = afx.AudioFadeIn if fade_in else afx.AudioFadeOut
                result = result.with_audio(
                    result.audio.with_effects([audio_effect(transition_duration)])
                )
            return result
        except (AttributeError, TypeError):
            video_effect: Callable[..., Any] = vfx.fadein if fade_in else vfx.fadeout
            result = clip.fx(video_effect, transition_duration)
            if result.audio is not None:
                audio_effect = afx.audio_fadein if fade_in else afx.audio_fadeout
                result = result.set_audio(
                    result.audio.fx(audio_effect, transition_duration)
                )
            return result

    @staticmethod
    def _apply_overlay(
        clip: Any,
        overlay: OverlaySpec,
        master_start: float,
        master_end: float,
        size: tuple[int, int],
        ImageClip: Any,
        CompositeVideoClip: Any,
        np: Any,
    ) -> Any:
        absolute_start = master_start if overlay.start is None else overlay.start
        absolute_end = master_end if overlay.end is None else overlay.end
        local_start = absolute_start - master_start
        duration = absolute_end - absolute_start
        overlay_height = max(100, size[1] // 4)
        image = ImageClip(
            _text_image(
                np,
                text=overlay.text,
                size=(size[0], overlay_height),
                font_size=max(24, size[1] // 25),
                lower_third=True,
            )
        )
        image = _call(image, "with_duration", "set_duration", duration)
        image = _call(image, "with_start", "set_start", local_start)
        position: object = {
            "top": ("center", 20),
            "center": "center",
            "bottom": ("center", size[1] - overlay_height - 20),
        }.get(overlay.position or "bottom", "bottom")
        image = _call(image, "with_position", "set_position", position)
        composite = CompositeVideoClip([clip, image], size=size)
        if clip.audio is not None:
            composite = _call(composite, "with_audio", "set_audio", clip.audio)
        return composite
