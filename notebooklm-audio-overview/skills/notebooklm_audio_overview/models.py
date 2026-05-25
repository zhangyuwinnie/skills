"""Typed models for the NotebookLM audio overview skill."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RequestValidationError(ValueError):
    """Validation error raised for malformed request payloads."""

    code: str
    message: str
    target: str | None = None

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict[str, str | None]:
        return {
            "code": self.code,
            "message": self.message,
            "target": self.target,
        }


@dataclass(frozen=True)
class RunWarning:
    """Structured warning emitted for degraded-but-successful cases."""

    code: str
    message: str
    target: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "code": self.code,
            "message": self.message,
            "target": self.target,
        }


@dataclass(frozen=True)
class RunError:
    """Structured error emitted for failed runs."""

    code: str
    message: str
    target: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "code": self.code,
            "message": self.message,
            "target": self.target,
        }


@dataclass(frozen=True)
class AudioOverviewRequest:
    """Normalized request model for generating one audio overview."""

    links: tuple[str, ...]
    notebook_name: str
    output_path: Path
    resume_notebook_id: str | None = None
    resume_artifact_id: str | None = None
    language: str = "en"
    audio_format: str | None = None
    audio_length: str | None = None
    episode_focus: str | None = None
    reuse_notebook: bool = False
    strict_mode: bool = False
    timeout_seconds: int = 300
    source_timeout_seconds: int = 300
    audio_timeout_seconds: int = 300
    poll_interval_seconds: float = 2.0
    overwrite: bool = False

    @property
    def is_resume(self) -> bool:
        return self.resume_notebook_id is not None and self.resume_artifact_id is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "links": list(self.links),
            "notebook_name": self.notebook_name,
            "output_path": str(self.output_path),
            "resume_notebook_id": self.resume_notebook_id,
            "resume_artifact_id": self.resume_artifact_id,
            "language": self.language,
            "audio_format": self.audio_format,
            "audio_length": self.audio_length,
            "episode_focus": self.episode_focus,
            "reuse_notebook": self.reuse_notebook,
            "strict_mode": self.strict_mode,
            "timeout_seconds": self.timeout_seconds,
            "source_timeout_seconds": self.source_timeout_seconds,
            "audio_timeout_seconds": self.audio_timeout_seconds,
            "poll_interval_seconds": self.poll_interval_seconds,
            "overwrite": self.overwrite,
        }


@dataclass(frozen=True)
class NotebookResult:
    """Notebook metadata returned by the skill."""

    id: str
    title: str
    reused: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "reused": self.reused,
        }


@dataclass(frozen=True)
class SourceResult:
    """Per-source status entry for the final result payload."""

    input_url: str
    normalized_url: str
    source_id: str | None = None
    title: str | None = None
    kind: str | None = None
    status: str = "pending"
    ready: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_url": self.input_url,
            "normalized_url": self.normalized_url,
            "source_id": self.source_id,
            "title": self.title,
            "kind": self.kind,
            "status": self.status,
            "ready": self.ready,
            "error": self.error,
        }


@dataclass(frozen=True)
class ArtifactResult:
    """Artifact metadata returned by the skill."""

    id: str
    kind: str = "audio"
    status: str = "pending"
    title: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "status": self.status,
            "title": self.title,
        }


@dataclass(frozen=True)
class AudioOverviewResult:
    """Stable JSON-serializable result for the skill."""

    ok: bool
    output_path: Path
    notebook: NotebookResult | None = None
    sources: list[SourceResult] = field(default_factory=list)
    artifact: ArtifactResult | None = None
    warnings: list[RunWarning] = field(default_factory=list)
    errors: list[RunError] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "notebook": self.notebook.to_dict() if self.notebook else None,
            "sources": [source.to_dict() for source in self.sources],
            "artifact": self.artifact.to_dict() if self.artifact else None,
            "output_path": str(self.output_path),
            "warnings": [warning.to_dict() for warning in self.warnings],
            "errors": [error.to_dict() for error in self.errors],
        }
