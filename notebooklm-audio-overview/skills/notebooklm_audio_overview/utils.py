"""Normalization utilities for the NotebookLM audio overview skill."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from urllib.parse import ParseResult, urlparse, urlunparse

from .models import RequestValidationError

AUDIO_FORMATS = {"deep-dive", "brief", "critique", "debate"}
AUDIO_LENGTHS = {"short", "default", "long"}
DEFAULT_OUTPUT_DIR = "output"


def normalize_url(raw_url: str) -> str:
    """Normalize a URL for validation and deduplication."""

    value = raw_url.strip()
    parsed = urlparse(value)

    if parsed.scheme.lower() not in {"http", "https"}:
        raise RequestValidationError(
            code="invalid_link",
            message=f"Unsupported URL scheme for link: {raw_url}",
            target="links",
        )
    if not parsed.netloc:
        raise RequestValidationError(
            code="invalid_link",
            message=f"URL must include a host: {raw_url}",
            target="links",
        )

    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").lower()
    port = parsed.port

    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{hostname}:{port}"
    else:
        netloc = hostname

    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    normalized = ParseResult(
        scheme=scheme,
        netloc=netloc,
        path=path,
        params="",
        query=parsed.query,
        fragment="",
    )
    return urlunparse(normalized)


def validate_audio_format(value: str | None) -> str | None:
    """Validate and normalize the audio format option."""

    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized not in AUDIO_FORMATS:
        raise RequestValidationError(
            code="invalid_audio_format",
            message=f"Unsupported audio_format: {value}",
            target="audio_format",
        )
    return normalized


def validate_audio_length(value: str | None) -> str | None:
    """Validate and normalize the audio length option."""

    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized not in AUDIO_LENGTHS:
        raise RequestValidationError(
            code="invalid_audio_length",
            message=f"Unsupported audio_length: {value}",
            target="audio_length",
        )
    return normalized


def slugify(value: str) -> str:
    """Create a filesystem-safe slug from a notebook name."""

    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "audio-overview"


def resolve_output_path(
    notebook_name: str,
    output_path: str | None = None,
    overwrite: bool = False,
) -> Path:
    """Resolve the target output path and apply the no-clobber policy."""

    if output_path:
        candidate = Path(output_path).expanduser()
    else:
        candidate = Path(DEFAULT_OUTPUT_DIR) / f"{slugify(notebook_name)}.mp3"

    if candidate.exists() and candidate.is_dir():
        raise RequestValidationError(
            code="invalid_output_path",
            message=f"Output path points to a directory: {candidate}",
            target="output_path",
        )

    resolved = candidate.resolve()
    if overwrite or not resolved.exists():
        return resolved

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return resolved.with_name(f"{resolved.stem}-{timestamp}{resolved.suffix}")
