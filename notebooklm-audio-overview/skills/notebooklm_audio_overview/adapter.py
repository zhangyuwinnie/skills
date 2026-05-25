"""NotebookLM adapter boundary for orchestration code."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from notebooklm import NotebookLMClient
from notebooklm.types import (
    Artifact,
    AudioFormat,
    AudioLength,
    GenerationStatus,
    Notebook,
    Source,
    source_status_to_str,
)


@dataclass(frozen=True)
class AdapterNotebook:
    """Minimal notebook metadata needed by the skill."""

    id: str
    title: str
    created_at: datetime | None = None


@dataclass(frozen=True)
class AdapterSource:
    """Normalized source state exposed to the orchestration layer."""

    id: str
    status: str = "pending"
    title: str | None = None
    kind: str | None = None
    url: str | None = None
    error: str | None = None

    @property
    def ready(self) -> bool:
        return self.status == "ready"


@dataclass(frozen=True)
class AdapterArtifact:
    """Normalized artifact state exposed to the orchestration layer."""

    id: str
    status: str = "pending"
    kind: str = "audio"
    title: str | None = None
    error: str | None = None


class NotebookLMAdapter(Protocol):
    """Contract used by the orchestration layer."""

    async def get_notebook(self, notebook_id: str) -> AdapterNotebook:
        """Fetch one notebook by ID."""

    async def list_notebooks(self) -> list[AdapterNotebook]:
        """List existing notebooks."""

    async def create_notebook(self, title: str) -> AdapterNotebook:
        """Create a notebook."""

    async def add_url_source(self, notebook_id: str, url: str) -> AdapterSource:
        """Add a URL source without waiting for readiness."""

    async def wait_for_source_ready(
        self,
        notebook_id: str,
        source_id: str,
        *,
        timeout: float,
        poll_interval: float,
    ) -> AdapterSource:
        """Wait for a source to reach a terminal ready state."""

    async def generate_audio(
        self,
        notebook_id: str,
        *,
        source_ids: list[str],
        language: str,
        instructions: str | None,
        audio_format: str | None,
        audio_length: str | None,
    ) -> AdapterArtifact:
        """Start audio generation."""

    async def wait_for_audio_completion(
        self,
        notebook_id: str,
        task_id: str,
        *,
        timeout: float,
        poll_interval: float,
    ) -> AdapterArtifact:
        """Wait for audio generation to reach a terminal state."""

    async def get_artifact(self, notebook_id: str, artifact_id: str) -> AdapterArtifact | None:
        """Fetch artifact metadata if available."""

    async def download_audio(
        self, notebook_id: str, artifact_id: str, output_path: Path
    ) -> Path:
        """Download the completed audio artifact."""

    async def close(self) -> None:
        """Release any adapter resources."""


class LiveNotebookLMAdapter:
    """Async adapter backed by the installed notebooklm-py client."""

    def __init__(self, *, storage_path: str | None = None, timeout: float = 30.0) -> None:
        self._storage_path = storage_path
        self._timeout = timeout
        self._client: NotebookLMClient | None = None

    async def get_notebook(self, notebook_id: str) -> AdapterNotebook:
        client = await self._get_client()
        notebook = await client.notebooks.get(notebook_id)
        return self._to_notebook(notebook)

    async def list_notebooks(self) -> list[AdapterNotebook]:
        client = await self._get_client()
        notebooks = await client.notebooks.list()
        return [self._to_notebook(item) for item in notebooks]

    async def create_notebook(self, title: str) -> AdapterNotebook:
        client = await self._get_client()
        notebook = await client.notebooks.create(title)
        return self._to_notebook(notebook)

    async def add_url_source(self, notebook_id: str, url: str) -> AdapterSource:
        client = await self._get_client()
        source = await client.sources.add_url(notebook_id, url, wait=False)
        current = await client.sources.get(notebook_id, source.id)
        if current is not None:
            return self._to_source(current)
        return AdapterSource(
            id=source.id,
            status="processing",
            title=source.title,
            kind=self._stringify_kind(source.kind),
            url=source.url or url,
        )

    async def wait_for_source_ready(
        self,
        notebook_id: str,
        source_id: str,
        *,
        timeout: float,
        poll_interval: float,
    ) -> AdapterSource:
        client = await self._get_client()
        source = await client.sources.wait_until_ready(
            notebook_id,
            source_id,
            timeout=timeout,
            initial_interval=poll_interval,
            max_interval=max(poll_interval, min(timeout, poll_interval * 4)),
            backoff_factor=1.5,
        )
        return self._to_source(source)

    async def generate_audio(
        self,
        notebook_id: str,
        *,
        source_ids: list[str],
        language: str,
        instructions: str | None,
        audio_format: str | None,
        audio_length: str | None,
    ) -> AdapterArtifact:
        client = await self._get_client()
        status = await client.artifacts.generate_audio(
            notebook_id,
            source_ids=source_ids,
            language=language,
            instructions=instructions,
            audio_format=self._map_audio_format(audio_format),
            audio_length=self._map_audio_length(audio_length),
        )
        return self._to_generation_artifact(status)

    async def wait_for_audio_completion(
        self,
        notebook_id: str,
        task_id: str,
        *,
        timeout: float,
        poll_interval: float,
    ) -> AdapterArtifact:
        client = await self._get_client()
        status = await client.artifacts.wait_for_completion(
            notebook_id,
            task_id,
            initial_interval=poll_interval,
            max_interval=max(poll_interval, min(timeout, poll_interval * 4)),
            timeout=timeout,
        )
        if status.is_complete:
            artifact = await client.artifacts.get(notebook_id, status.task_id)
            if artifact is not None:
                return self._to_artifact(artifact)
        return self._to_generation_artifact(status)

    async def get_artifact(self, notebook_id: str, artifact_id: str) -> AdapterArtifact | None:
        client = await self._get_client()
        artifact = await client.artifacts.get(notebook_id, artifact_id)
        if artifact is None:
            return None
        return self._to_artifact(artifact)

    async def download_audio(
        self, notebook_id: str, artifact_id: str, output_path: Path
    ) -> Path:
        client = await self._get_client()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        saved_path = await client.artifacts.download_audio(
            notebook_id,
            str(output_path),
            artifact_id=artifact_id,
        )
        return Path(saved_path).resolve()

    async def close(self) -> None:
        if self._client is None:
            return
        await self._client.__aexit__(None, None, None)
        self._client = None

    async def _get_client(self) -> NotebookLMClient:
        if self._client is None:
            client = await NotebookLMClient.from_storage(
                path=self._storage_path,
                timeout=self._timeout,
            )
            self._client = await client.__aenter__()
        return self._client

    @staticmethod
    def _to_notebook(notebook: Notebook) -> AdapterNotebook:
        return AdapterNotebook(
            id=notebook.id,
            title=notebook.title,
            created_at=notebook.created_at,
        )

    @classmethod
    def _to_source(cls, source: Source) -> AdapterSource:
        return AdapterSource(
            id=source.id,
            status=source_status_to_str(source.status),
            title=source.title,
            kind=cls._stringify_kind(source.kind),
            url=source.url,
        )

    @classmethod
    def _to_artifact(cls, artifact: Artifact) -> AdapterArtifact:
        return AdapterArtifact(
            id=artifact.id,
            status=artifact.status_str,
            kind=cls._stringify_kind(artifact.kind),
            title=artifact.title,
        )

    @staticmethod
    def _to_generation_artifact(status: GenerationStatus) -> AdapterArtifact:
        return AdapterArtifact(
            id=status.task_id,
            status=status.status,
            kind="audio",
            error=status.error,
        )

    @staticmethod
    def _stringify_kind(kind: object) -> str | None:
        value = getattr(kind, "value", kind)
        if value is None:
            return None
        return str(value)

    @staticmethod
    def _map_audio_format(value: str | None) -> AudioFormat | None:
        if value is None:
            return None
        mapping = {
            "deep-dive": AudioFormat.DEEP_DIVE,
            "brief": AudioFormat.BRIEF,
            "critique": AudioFormat.CRITIQUE,
            "debate": AudioFormat.DEBATE,
        }
        return mapping[value]

    @staticmethod
    def _map_audio_length(value: str | None) -> AudioLength | None:
        if value is None:
            return None
        mapping = {
            "short": AudioLength.SHORT,
            "default": AudioLength.DEFAULT,
            "long": AudioLength.LONG,
        }
        return mapping[value]
