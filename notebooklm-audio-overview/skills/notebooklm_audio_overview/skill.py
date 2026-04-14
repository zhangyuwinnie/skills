"""Request normalization and orchestration for the skill."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from .adapter import (
    AdapterArtifact,
    AdapterNotebook,
    AdapterSource,
    LiveNotebookLMAdapter,
    NotebookLMAdapter,
)
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
from .utils import (
    resolve_output_path,
    validate_audio_format,
    validate_audio_length,
    normalize_url,
)

MAX_SOURCE_ADD_ATTEMPTS = 3


def normalize_request(payload: Mapping[str, Any]) -> AudioOverviewRequest:
    """Validate and normalize an untrusted request payload."""

    if not isinstance(payload, Mapping):
        raise RequestValidationError(
            code="invalid_request",
            message="Request payload must be a mapping.",
            target="request",
        )

    overwrite = _get_bool(payload, "overwrite", default=False)
    resume_notebook_id = _get_optional_string(payload, "resume_notebook_id")
    resume_artifact_id = _get_optional_string(payload, "resume_artifact_id")
    resume_requested = resume_notebook_id is not None or resume_artifact_id is not None

    notebook_name = _get_optional_string(payload, "notebook_name")
    normalized_links: list[str] = []

    if resume_requested:
        if resume_notebook_id is None:
            raise RequestValidationError(
                code="missing_resume_notebook_id",
                message="resume_notebook_id is required when resume_artifact_id is provided.",
                target="resume_notebook_id",
            )
        if resume_artifact_id is None:
            raise RequestValidationError(
                code="missing_resume_artifact_id",
                message="resume_artifact_id is required when resume_notebook_id is provided.",
                target="resume_artifact_id",
            )
        output_path_value = _require_non_empty_string(payload.get("output_path"), "output_path")
        if notebook_name is None:
            notebook_name = "Resumed NotebookLM Audio"
    else:
        raw_links = payload.get("links")
        if not isinstance(raw_links, list) or not raw_links:
            raise RequestValidationError(
                code="missing_links",
                message="links must be a non-empty list of HTTP/HTTPS URLs.",
                target="links",
            )

        notebook_name = _require_non_empty_string(payload.get("notebook_name"), "notebook_name")
        seen_links: set[str] = set()
        for item in raw_links:
            if not isinstance(item, str):
                raise RequestValidationError(
                    code="invalid_link",
                    message=f"Link values must be strings: {item!r}",
                    target="links",
                )
            normalized = normalize_url(item)
            if normalized not in seen_links:
                seen_links.add(normalized)
                normalized_links.append(normalized)
        output_path_value = _get_optional_string(payload, "output_path")

    timeout_seconds = _get_positive_int(payload, "timeout_seconds", default=300)
    source_timeout_seconds = _get_positive_int(
        payload,
        "source_timeout_seconds",
        default=timeout_seconds,
    )
    audio_timeout_seconds = _get_positive_int(
        payload,
        "audio_timeout_seconds",
        default=timeout_seconds,
    )

    return AudioOverviewRequest(
        links=tuple(normalized_links),
        notebook_name=notebook_name,
        output_path=resolve_output_path(
            notebook_name=notebook_name,
            output_path=output_path_value,
            overwrite=overwrite,
        ),
        resume_notebook_id=resume_notebook_id,
        resume_artifact_id=resume_artifact_id,
        language=_get_optional_string(payload, "language", default="en"),
        audio_format=validate_audio_format(_get_optional_string(payload, "audio_format")),
        audio_length=validate_audio_length(_get_optional_string(payload, "audio_length")),
        episode_focus=_get_optional_string(payload, "episode_focus"),
        reuse_notebook=_get_bool(payload, "reuse_notebook", default=False),
        strict_mode=_get_bool(payload, "strict_mode", default=False),
        timeout_seconds=timeout_seconds,
        source_timeout_seconds=source_timeout_seconds,
        audio_timeout_seconds=audio_timeout_seconds,
        poll_interval_seconds=_get_positive_number(
            payload, "poll_interval_seconds", default=2.0
        ),
        overwrite=overwrite,
    )


def create_result(
    request: AudioOverviewRequest,
    *,
    ok: bool = False,
    output_path: Path | None = None,
    notebook: NotebookResult | None = None,
    sources: list[SourceResult] | None = None,
    artifact: ArtifactResult | None = None,
    warnings: list[RunWarning] | None = None,
    errors: list[RunError] | None = None,
) -> AudioOverviewResult:
    """Create a stable result object for JSON serialization."""

    return AudioOverviewResult(
        ok=ok,
        output_path=request.output_path if output_path is None else output_path,
        notebook=notebook,
        sources=list(sources or []),
        artifact=artifact,
        warnings=list(warnings or []),
        errors=list(errors or []),
    )


async def generate_audio_overview(
    request: AudioOverviewRequest,
    *,
    adapter: NotebookLMAdapter | None = None,
) -> AudioOverviewResult:
    """Run the NotebookLM orchestration for a normalized request."""

    warnings: list[RunWarning] = []
    errors: list[RunError] = []
    notebook: NotebookResult | None = None
    artifact: ArtifactResult | None = None
    sources = [
        SourceResult(input_url=link, normalized_url=link)
        for link in request.links
    ]

    own_adapter = adapter is None
    active_adapter = adapter or LiveNotebookLMAdapter()

    try:
        if request.is_resume:
            notebook, artifact, resume_error = await _resume_existing_artifact(
                active_adapter,
                request=request,
            )
            if notebook is not None:
                request.output_path.parent.mkdir(parents=True, exist_ok=True)
            if resume_error is not None:
                errors.append(resume_error)
                return create_result(
                    request,
                    ok=False,
                    notebook=notebook,
                    sources=sources,
                    artifact=artifact,
                    warnings=warnings,
                    errors=errors,
                )

            downloaded_path = await active_adapter.download_audio(
                notebook.id,
                artifact.id,
                request.output_path,
            )
            return create_result(
                request,
                ok=True,
                output_path=downloaded_path,
                notebook=notebook,
                sources=sources,
                artifact=artifact,
                warnings=warnings,
                errors=errors,
            )

        notebook, notebook_warnings = await _ensure_notebook(active_adapter, request)
        warnings.extend(notebook_warnings)

        sources = await _ingest_sources(
            active_adapter,
            notebook_id=notebook.id,
            sources=sources,
        )
        sources = await _wait_for_sources(
            active_adapter,
            request=request,
            notebook_id=notebook.id,
            sources=sources,
        )

        ready_source_ids = [source.source_id for source in sources if source.ready and source.source_id]
        failed_sources = [source for source in sources if not source.ready]

        if request.strict_mode and failed_sources:
            errors.append(
                RunError(
                    code="strict_mode_source_failure",
                    message="strict_mode requires every source to become ready.",
                    target="links",
                )
            )
            return create_result(
                request,
                ok=False,
                notebook=notebook,
                sources=sources,
                warnings=warnings,
                errors=errors,
            )

        if not ready_source_ids:
            errors.append(
                RunError(
                    code="no_sources_ready",
                    message="NotebookLM did not produce any ready sources.",
                    target="links",
                )
            )
            return create_result(
                request,
                ok=False,
                notebook=notebook,
                sources=sources,
                warnings=warnings,
                errors=errors,
            )

        if failed_sources:
            warnings.append(
                RunWarning(
                    code="partial_source_failure",
                    message=(
                        f"{len(failed_sources)} source(s) failed or did not become ready. "
                        f"Continuing with {len(ready_source_ids)} ready source(s)."
                    ),
                    target="links",
                )
            )

        artifact, audio_error = await _generate_audio_artifact(
            active_adapter,
            request=request,
            notebook_id=notebook.id,
            source_ids=[source_id for source_id in ready_source_ids if source_id is not None],
        )
        if audio_error is not None:
            errors.append(audio_error)
            return create_result(
                request,
                ok=False,
                notebook=notebook,
                sources=sources,
                artifact=artifact,
                warnings=warnings,
                errors=errors,
            )

        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        downloaded_path = await active_adapter.download_audio(
            notebook.id,
            artifact.id,
            request.output_path,
        )
        return create_result(
            request,
            ok=True,
            output_path=downloaded_path,
            notebook=notebook,
            sources=sources,
            artifact=artifact,
            warnings=warnings,
            errors=errors,
        )
    except Exception as exc:
        errors.append(_runtime_error(exc))
        return create_result(
            request,
            ok=False,
            notebook=notebook,
            sources=sources,
            artifact=artifact,
            warnings=warnings,
            errors=errors,
        )
    finally:
        if own_adapter:
            await active_adapter.close()


def generate_audio_overview_from_links(
    payload: Mapping[str, Any] | AudioOverviewRequest,
) -> AudioOverviewResult:
    """Synchronous wrapper for library and CLI callers."""

    request = payload if isinstance(payload, AudioOverviewRequest) else normalize_request(payload)
    return asyncio.run(generate_audio_overview(request))


async def _ensure_notebook(
    adapter: NotebookLMAdapter,
    request: AudioOverviewRequest,
) -> tuple[NotebookResult, list[RunWarning]]:
    warnings: list[RunWarning] = []
    if not request.reuse_notebook:
        created = await adapter.create_notebook(request.notebook_name)
        return NotebookResult(id=created.id, title=created.title, reused=False), warnings

    matches = [
        notebook
        for notebook in await adapter.list_notebooks()
        if notebook.title == request.notebook_name
    ]
    if not matches:
        created = await adapter.create_notebook(request.notebook_name)
        return NotebookResult(id=created.id, title=created.title, reused=False), warnings

    chosen = _choose_most_recent_notebook(matches)
    if len(matches) > 1:
        warnings.append(
            RunWarning(
                code="multiple_matching_notebooks",
                message=(
                    f"Found {len(matches)} notebooks named {request.notebook_name!r}. "
                    "Reusing the most recently created match."
                ),
                target="notebook_name",
            )
        )
    return NotebookResult(id=chosen.id, title=chosen.title, reused=True), warnings


async def _resume_existing_artifact(
    adapter: NotebookLMAdapter,
    *,
    request: AudioOverviewRequest,
) -> tuple[NotebookResult | None, ArtifactResult | None, RunError | None]:
    notebook_id = request.resume_notebook_id
    artifact_id = request.resume_artifact_id
    if notebook_id is None or artifact_id is None:
        return None, None, RunError(
            code="invalid_resume_request",
            message="Resume mode requires both notebook and artifact IDs.",
            target="request",
        )

    notebook_meta = await adapter.get_notebook(notebook_id)
    notebook = NotebookResult(id=notebook_meta.id, title=notebook_meta.title, reused=True)

    current = await adapter.get_artifact(notebook_id, artifact_id)
    if current is None:
        return notebook, None, RunError(
            code="artifact_not_found",
            message="NotebookLM artifact was not found for the requested notebook.",
            target=artifact_id,
        )

    if current.status == "completed":
        artifact = await _resolve_artifact(adapter, notebook_id, current)
        return notebook, artifact, None

    if current.status in {"failed", "error"}:
        return notebook, _to_artifact_result(current), RunError(
            code="audio_generation_failed",
            message=current.error or "NotebookLM audio generation did not complete successfully.",
            target=artifact_id,
        )

    try:
        completed = await adapter.wait_for_audio_completion(
            notebook_id,
            artifact_id,
            timeout=request.audio_timeout_seconds,
            poll_interval=request.poll_interval_seconds,
        )
    except TimeoutError as exc:
        return notebook, _to_artifact_result(current), RunError(
            code="audio_generation_timeout",
            message=str(exc),
            target=artifact_id,
        )
    except Exception as exc:
        return notebook, _to_artifact_result(current), RunError(
            code="audio_generation_failed",
            message=str(exc),
            target=artifact_id,
        )

    artifact = await _resolve_artifact(adapter, notebook_id, completed)
    if artifact.status != "completed":
        return notebook, artifact, RunError(
            code="audio_generation_failed",
            message="NotebookLM audio generation did not complete successfully.",
            target=artifact.id,
        )

    return notebook, artifact, None


async def _ingest_sources(
    adapter: NotebookLMAdapter,
    *,
    notebook_id: str,
    sources: list[SourceResult],
) -> list[SourceResult]:
    updated_sources: list[SourceResult] = []
    for source in sources:
        current = source
        for attempt in range(MAX_SOURCE_ADD_ATTEMPTS):
            try:
                ingested = await adapter.add_url_source(notebook_id, source.normalized_url)
                current = _merge_source_state(source, ingested)
                break
            except Exception as exc:
                current = replace(
                    source,
                    status="error",
                    ready=False,
                    error=str(exc),
                )
                if attempt == MAX_SOURCE_ADD_ATTEMPTS - 1:
                    break
        updated_sources.append(current)
    return updated_sources


async def _wait_for_sources(
    adapter: NotebookLMAdapter,
    *,
    request: AudioOverviewRequest,
    notebook_id: str,
    sources: list[SourceResult],
) -> list[SourceResult]:
    async def wait_for_one(source: SourceResult) -> SourceResult:
        if not source.source_id or source.error is not None:
            return source
        try:
            ready_source = await adapter.wait_for_source_ready(
                notebook_id,
                source.source_id,
                timeout=request.source_timeout_seconds,
                poll_interval=request.poll_interval_seconds,
            )
            return _merge_source_state(source, ready_source)
        except TimeoutError as exc:
            return replace(source, status="timeout", ready=False, error=str(exc))
        except Exception as exc:
            return replace(source, status="error", ready=False, error=str(exc))

    return list(await asyncio.gather(*(wait_for_one(source) for source in sources)))


async def _generate_audio_artifact(
    adapter: NotebookLMAdapter,
    *,
    request: AudioOverviewRequest,
    notebook_id: str,
    source_ids: list[str],
) -> tuple[ArtifactResult | None, RunError | None]:
    try:
        started = await adapter.generate_audio(
            notebook_id,
            source_ids=source_ids,
            language=request.language,
            instructions=request.episode_focus,
            audio_format=request.audio_format,
            audio_length=request.audio_length,
        )
    except Exception as exc:
        return None, RunError(
            code="audio_generation_failed",
            message=str(exc),
            target="artifact",
        )

    try:
        completed = await adapter.wait_for_audio_completion(
            notebook_id,
            started.id,
            timeout=request.audio_timeout_seconds,
            poll_interval=request.poll_interval_seconds,
        )
    except TimeoutError as exc:
        return _to_artifact_result(started), RunError(
            code="audio_generation_timeout",
            message=str(exc),
            target=started.id,
        )
    except Exception as exc:
        return _to_artifact_result(started), RunError(
            code="audio_generation_failed",
            message=str(exc),
            target=started.id,
        )

    artifact = await _resolve_artifact(adapter, notebook_id, completed)
    if artifact.status != "completed":
        return artifact, RunError(
            code="audio_generation_failed",
            message=completed.error or "NotebookLM audio generation did not complete successfully.",
            target=artifact.id,
        )

    return artifact, None


async def _resolve_artifact(
    adapter: NotebookLMAdapter,
    notebook_id: str,
    artifact: AdapterArtifact,
) -> ArtifactResult:
    current = artifact
    if artifact.status == "completed":
        fetched = await adapter.get_artifact(notebook_id, artifact.id)
        if fetched is not None:
            current = fetched
    return _to_artifact_result(current)


def _merge_source_state(source: SourceResult, state: AdapterSource) -> SourceResult:
    return SourceResult(
        input_url=source.input_url,
        normalized_url=source.normalized_url,
        source_id=state.id,
        title=state.title,
        kind=state.kind,
        status=state.status,
        ready=state.ready,
        error=state.error,
    )


def _choose_most_recent_notebook(matches: list[AdapterNotebook]) -> AdapterNotebook:
    dated_matches = []
    for index, notebook in enumerate(matches):
        created_at = notebook.created_at or datetime.min
        dated_matches.append((created_at, index, notebook))
    dated_matches.sort(key=lambda item: (item[0], item[1]))
    return dated_matches[-1][2]


def _to_artifact_result(artifact: AdapterArtifact) -> ArtifactResult:
    return ArtifactResult(
        id=artifact.id,
        kind=artifact.kind,
        status=artifact.status,
        title=artifact.title,
    )


def _runtime_error(exc: Exception) -> RunError:
    if isinstance(exc, FileNotFoundError):
        return RunError(
            code="authentication_required",
            message=str(exc),
            target="notebooklm login",
        )
    return RunError(
        code="notebooklm_runtime_error",
        message=str(exc),
        target=None,
    )


def _require_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RequestValidationError(
            code=f"invalid_{field_name}",
            message=f"{field_name} must be a non-empty string.",
            target=field_name,
        )
    return value.strip()


def _get_optional_string(
    payload: Mapping[str, Any], field_name: str, default: str | None = None
) -> str | None:
    value = payload.get(field_name, default)
    if value is None:
        return None
    if not isinstance(value, str):
        raise RequestValidationError(
            code=f"invalid_{field_name}",
            message=f"{field_name} must be a string.",
            target=field_name,
        )
    stripped = value.strip()
    return stripped or default


def _get_bool(payload: Mapping[str, Any], field_name: str, default: bool) -> bool:
    value = payload.get(field_name, default)
    if not isinstance(value, bool):
        raise RequestValidationError(
            code=f"invalid_{field_name}",
            message=f"{field_name} must be a boolean.",
            target=field_name,
        )
    return value


def _get_positive_int(payload: Mapping[str, Any], field_name: str, default: int) -> int:
    value = payload.get(field_name, default)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise RequestValidationError(
            code=f"invalid_{field_name}",
            message=f"{field_name} must be a positive integer.",
            target=field_name,
        )
    return value


def _get_positive_number(
    payload: Mapping[str, Any], field_name: str, default: float
) -> float:
    value = payload.get(field_name, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise RequestValidationError(
            code=f"invalid_{field_name}",
            message=f"{field_name} must be a positive number.",
            target=field_name,
        )
    return float(value)
