"""Domain-specific exceptions with actionable user-facing messages."""


class PipelineError(Exception):
    """Base class for expected pipeline failures."""


class ConfigurationError(PipelineError):
    """Project or synchronisation configuration is invalid."""


class InputFileError(PipelineError):
    """An input path is missing, unsafe, unreadable, or unsupported."""


class PreflightError(PipelineError):
    """A required Python package or executable is unavailable."""


class MediaProbeError(PipelineError):
    """FFprobe could not read usable metadata."""


class SyncValidationError(PipelineError):
    """Clap timestamps or calculated offsets are invalid."""


class EDLParseError(PipelineError):
    """The EDL cannot be parsed as the supported JSON contract."""


class EDLValidationError(PipelineError):
    """The EDL is syntactically valid JSON but semantically invalid."""


class RenderPlanError(PipelineError):
    """A validated EDL cannot be mapped safely to source media."""


class RendererError(PipelineError):
    """Base class for rendering backend failures."""


class MoviePyRenderError(RendererError):
    """MoviePy failed for a renderer-specific reason."""


class FFmpegRenderError(RendererError):
    """FFmpeg failed for a renderer-specific reason."""


class OutputValidationError(PipelineError):
    """A rendered output does not satisfy technical requirements."""


class ReviewError(PipelineError):
    """A human review record is missing or invalid."""


class ApprovalError(PipelineError):
    """A draft cannot be promoted under the supplied approval."""


class PreparationError(PipelineError):
    """Automatic preparation cannot safely produce the requested artefact."""
