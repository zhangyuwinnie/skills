"""NotebookLM audio overview skill package."""

__version__ = "0.1.0"

from .models import (
    ArtifactResult,
    AudioOverviewRequest,
    AudioOverviewResult,
    NotebookResult,
    RequestValidationError,
    RunError,
    RunWarning,
    SourceResult,
)
from .skill import (
    create_result,
    generate_audio_overview,
    generate_audio_overview_from_links,
    normalize_request,
)

__all__ = [
    "__version__",
    "ArtifactResult",
    "AudioOverviewRequest",
    "AudioOverviewResult",
    "NotebookResult",
    "RequestValidationError",
    "RunError",
    "RunWarning",
    "SourceResult",
    "create_result",
    "generate_audio_overview",
    "generate_audio_overview_from_links",
    "normalize_request",
]
