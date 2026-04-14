import asyncio
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from skills.notebooklm_audio_overview.adapter import (
    AdapterArtifact,
    AdapterNotebook,
    AdapterSource,
)
from skills.notebooklm_audio_overview.skill import (
    generate_audio_overview,
    normalize_request,
)


class FakeAdapter:
    def __init__(
        self,
        *,
        notebooks: Iterable[AdapterNotebook] = (),
        add_sequences: dict[str, list[object]] | None = None,
        wait_results: dict[str, object] | None = None,
        generation_result: AdapterArtifact | Exception | None = None,
        completion_result: AdapterArtifact | Exception | None = None,
        artifact_lookup: dict[str, AdapterArtifact | list[AdapterArtifact]] | None = None,
        download_result: Path | Exception | None = None,
    ) -> None:
        self._notebooks = list(notebooks)
        self._add_sequences = {key: list(value) for key, value in (add_sequences or {}).items()}
        self._wait_results = dict(wait_results or {})
        self._generation_result = generation_result or AdapterArtifact(
            id="art_default",
            status="in_progress",
            kind="audio",
            title="Audio Overview",
        )
        self._completion_result = completion_result or AdapterArtifact(
            id="art_default",
            status="completed",
            kind="audio",
            title="Audio Overview",
        )
        self._artifact_lookup = {
            key: list(value) if isinstance(value, list) else value
            for key, value in (artifact_lookup or {}).items()
        }
        self._download_result = download_result
        self.calls: list[tuple[object, ...]] = []
        self._created_count = 0

    async def list_notebooks(self) -> list[AdapterNotebook]:
        self.calls.append(("list_notebooks",))
        return list(self._notebooks)

    async def get_notebook(self, notebook_id: str) -> AdapterNotebook:
        self.calls.append(("get_notebook", notebook_id))
        for notebook in self._notebooks:
            if notebook.id == notebook_id:
                return notebook
        raise KeyError(notebook_id)

    async def create_notebook(self, title: str) -> AdapterNotebook:
        self.calls.append(("create_notebook", title))
        self._created_count += 1
        notebook = AdapterNotebook(id=f"nb_created_{self._created_count}", title=title)
        self._notebooks.append(notebook)
        return notebook

    async def add_url_source(self, notebook_id: str, url: str) -> AdapterSource:
        self.calls.append(("add_url_source", notebook_id, url))
        queue = self._add_sequences.get(url)
        if queue:
            outcome = queue.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome
        return AdapterSource(id=f"src_{len(self.calls)}", status="processing", url=url)

    async def wait_for_source_ready(
        self,
        notebook_id: str,
        source_id: str,
        *,
        timeout: float,
        poll_interval: float,
    ) -> AdapterSource:
        self.calls.append(("wait_for_source_ready", notebook_id, source_id, timeout, poll_interval))
        outcome = self._wait_results.get(source_id)
        if isinstance(outcome, Exception):
            raise outcome
        if outcome is None:
            return AdapterSource(id=source_id, status="ready")
        return outcome

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
        self.calls.append(
            (
                "generate_audio",
                notebook_id,
                tuple(source_ids),
                language,
                instructions,
                audio_format,
                audio_length,
            )
        )
        if isinstance(self._generation_result, Exception):
            raise self._generation_result
        return self._generation_result

    async def wait_for_audio_completion(
        self,
        notebook_id: str,
        task_id: str,
        *,
        timeout: float,
        poll_interval: float,
    ) -> AdapterArtifact:
        self.calls.append(("wait_for_audio_completion", notebook_id, task_id, timeout, poll_interval))
        if isinstance(self._completion_result, Exception):
            raise self._completion_result
        return self._completion_result

    async def get_artifact(self, notebook_id: str, artifact_id: str) -> AdapterArtifact | None:
        self.calls.append(("get_artifact", notebook_id, artifact_id))
        outcome = self._artifact_lookup.get(artifact_id)
        if isinstance(outcome, list):
            if not outcome:
                return None
            return outcome.pop(0)
        return outcome

    async def download_audio(
        self, notebook_id: str, artifact_id: str, output_path: Path
    ) -> Path:
        self.calls.append(("download_audio", notebook_id, artifact_id, output_path))
        if isinstance(self._download_result, Exception):
            raise self._download_result
        return self._download_result or output_path

    async def close(self) -> None:
        self.calls.append(("close",))


def test_reuses_most_recent_exact_match_and_warns_for_duplicate_titles(tmp_path: Path) -> None:
    older = AdapterNotebook(
        id="nb_old",
        title="Research Briefing",
        created_at=datetime(2026, 3, 20, 8, 0, 0),
    )
    newer = AdapterNotebook(
        id="nb_new",
        title="Research Briefing",
        created_at=datetime(2026, 3, 21, 8, 0, 0),
    )
    adapter = FakeAdapter(
        notebooks=[older, newer],
        add_sequences={
            "https://example.com/article": [
                AdapterSource(id="src_1", status="processing", url="https://example.com/article")
            ]
        },
        wait_results={
            "src_1": AdapterSource(
                id="src_1",
                status="ready",
                title="Example Article",
                kind="web_page",
                url="https://example.com/article",
            )
        },
        generation_result=AdapterArtifact(id="art_1", status="in_progress", kind="audio"),
        completion_result=AdapterArtifact(
            id="art_1",
            status="completed",
            kind="audio",
            title="Audio Overview",
        ),
        artifact_lookup={
            "art_1": AdapterArtifact(
                id="art_1",
                status="completed",
                kind="audio",
                title="Audio Overview",
            )
        },
    )

    request = normalize_request(
        {
            "links": ["https://example.com/article"],
            "notebook_name": "Research Briefing",
            "output_path": str(tmp_path / "briefing.mp3"),
            "reuse_notebook": True,
        }
    )

    result = asyncio.run(generate_audio_overview(request, adapter=adapter))

    assert result.ok is True
    assert result.notebook is not None
    assert result.notebook.id == "nb_new"
    assert result.notebook.reused is True
    assert [warning.code for warning in result.warnings] == ["multiple_matching_notebooks"]
    assert ("create_notebook", "Research Briefing") not in adapter.calls


def test_retries_source_ingestion_and_continues_with_partial_failure_in_non_strict_mode(
    tmp_path: Path,
) -> None:
    adapter = FakeAdapter(
        add_sequences={
            "https://example.com/a": [
                RuntimeError("temporary add failure"),
                AdapterSource(id="src_a", status="processing", url="https://example.com/a"),
            ],
            "https://example.com/b": [
                RuntimeError("permanent add failure"),
                RuntimeError("permanent add failure"),
                RuntimeError("permanent add failure"),
            ],
        },
        wait_results={
            "src_a": AdapterSource(
                id="src_a",
                status="ready",
                title="Source A",
                kind="web_page",
                url="https://example.com/a",
            )
        },
        generation_result=AdapterArtifact(id="art_2", status="in_progress", kind="audio"),
        completion_result=AdapterArtifact(
            id="art_2",
            status="completed",
            kind="audio",
            title="Overview A",
        ),
    )
    request = normalize_request(
        {
            "links": ["https://example.com/a", "https://example.com/b"],
            "notebook_name": "Batch 3 Retry",
            "output_path": str(tmp_path / "retry.mp3"),
        }
    )

    result = asyncio.run(generate_audio_overview(request, adapter=adapter))

    assert result.ok is True
    assert result.errors == []
    assert [warning.code for warning in result.warnings] == ["partial_source_failure"]
    assert [source.ready for source in result.sources] == [True, False]
    assert result.sources[1].error == "permanent add failure"
    assert adapter.calls.count(("add_url_source", "nb_created_1", "https://example.com/a")) == 2
    assert adapter.calls.count(("add_url_source", "nb_created_1", "https://example.com/b")) == 3
    assert (
        "generate_audio",
        "nb_created_1",
        ("src_a",),
        "en",
        None,
        None,
        None,
    ) in adapter.calls


def test_strict_mode_fails_when_any_source_is_not_ready(tmp_path: Path) -> None:
    adapter = FakeAdapter(
        add_sequences={
            "https://example.com/a": [
                AdapterSource(id="src_a", status="processing", url="https://example.com/a")
            ],
            "https://example.com/b": [
                AdapterSource(id="src_b", status="processing", url="https://example.com/b")
            ],
        },
        wait_results={
            "src_a": AdapterSource(id="src_a", status="ready", url="https://example.com/a"),
            "src_b": TimeoutError("source wait timed out"),
        },
    )
    request = normalize_request(
        {
            "links": ["https://example.com/a", "https://example.com/b"],
            "notebook_name": "Strict Mode",
            "output_path": str(tmp_path / "strict.mp3"),
            "strict_mode": True,
        }
    )

    result = asyncio.run(generate_audio_overview(request, adapter=adapter))

    assert result.ok is False
    assert [error.code for error in result.errors] == ["strict_mode_source_failure"]
    assert all(call[0] != "generate_audio" for call in adapter.calls)
    assert result.sources[1].status == "timeout"


def test_uses_separate_source_and_audio_timeouts(tmp_path: Path) -> None:
    output_path = (tmp_path / "split-timeouts.mp3").resolve()
    adapter = FakeAdapter(
        add_sequences={
            "https://example.com/a": [
                AdapterSource(id="src_a", status="processing", url="https://example.com/a")
            ]
        },
        wait_results={
            "src_a": AdapterSource(
                id="src_a",
                status="ready",
                title="Source A",
                kind="web_page",
                url="https://example.com/a",
            )
        },
        generation_result=AdapterArtifact(id="art_split", status="in_progress", kind="audio"),
        completion_result=AdapterArtifact(
            id="art_split",
            status="completed",
            kind="audio",
            title="Split Timeout Audio",
        ),
        artifact_lookup={
            "art_split": AdapterArtifact(
                id="art_split",
                status="completed",
                kind="audio",
                title="Split Timeout Audio",
            )
        },
        download_result=output_path,
    )
    request = normalize_request(
        {
            "links": ["https://example.com/a"],
            "notebook_name": "Split Timeouts",
            "output_path": str(output_path),
            "source_timeout_seconds": 45,
            "audio_timeout_seconds": 900,
            "poll_interval_seconds": 4,
        }
    )

    result = asyncio.run(generate_audio_overview(request, adapter=adapter))

    assert result.ok is True
    assert ("wait_for_source_ready", "nb_created_1", "src_a", 45, 4.0) in adapter.calls
    assert ("wait_for_audio_completion", "nb_created_1", "art_split", 900, 4.0) in adapter.calls


def test_resume_mode_waits_for_existing_artifact_and_downloads(tmp_path: Path) -> None:
    output_path = (tmp_path / "resumed.mp3").resolve()
    adapter = FakeAdapter(
        notebooks=[AdapterNotebook(id="nb_resume", title="Resume Notebook")],
        artifact_lookup={
            "art_resume": [
                AdapterArtifact(id="art_resume", status="pending", kind="audio"),
                AdapterArtifact(
                    id="art_resume",
                    status="completed",
                    kind="audio",
                    title="Resumed Audio",
                ),
            ]
        },
        completion_result=AdapterArtifact(
            id="art_resume",
            status="completed",
            kind="audio",
            title="Resumed Audio",
        ),
        download_result=output_path,
    )
    request = normalize_request(
        {
            "resume_notebook_id": "nb_resume",
            "resume_artifact_id": "art_resume",
            "output_path": str(output_path),
            "audio_timeout_seconds": 900,
            "poll_interval_seconds": 4,
        }
    )

    result = asyncio.run(generate_audio_overview(request, adapter=adapter))

    assert result.ok is True
    assert result.notebook is not None
    assert result.notebook.id == "nb_resume"
    assert result.sources == []
    assert result.artifact is not None
    assert result.artifact.id == "art_resume"
    assert ("get_notebook", "nb_resume") in adapter.calls
    assert ("wait_for_audio_completion", "nb_resume", "art_resume", 900, 4.0) in adapter.calls
    assert ("download_audio", "nb_resume", "art_resume", output_path) in adapter.calls
    assert all(call[0] != "create_notebook" for call in adapter.calls)
    assert all(call[0] != "generate_audio" for call in adapter.calls)


def test_resume_mode_reports_missing_artifact_without_download(tmp_path: Path) -> None:
    adapter = FakeAdapter(
        notebooks=[AdapterNotebook(id="nb_resume", title="Resume Notebook")],
        artifact_lookup={},
    )
    request = normalize_request(
        {
            "resume_notebook_id": "nb_resume",
            "resume_artifact_id": "art_missing",
            "output_path": str(tmp_path / "missing.mp3"),
        }
    )

    result = asyncio.run(generate_audio_overview(request, adapter=adapter))

    assert result.ok is False
    assert [error.code for error in result.errors] == ["artifact_not_found"]
    assert all(call[0] != "download_audio" for call in adapter.calls)


def test_audio_generation_uses_request_options_and_downloads_output(tmp_path: Path) -> None:
    output_path = (tmp_path / "overview.mp3").resolve()
    adapter = FakeAdapter(
        add_sequences={
            "https://example.com/a": [
                AdapterSource(id="src_a", status="processing", url="https://example.com/a")
            ]
        },
        wait_results={
            "src_a": AdapterSource(
                id="src_a",
                status="ready",
                title="Source A",
                kind="web_page",
                url="https://example.com/a",
            )
        },
        generation_result=AdapterArtifact(id="art_3", status="in_progress", kind="audio"),
        completion_result=AdapterArtifact(
            id="art_3",
            status="completed",
            kind="audio",
            title="Focused Audio",
        ),
        artifact_lookup={
            "art_3": AdapterArtifact(
                id="art_3",
                status="completed",
                kind="audio",
                title="Focused Audio",
            )
        },
        download_result=output_path,
    )
    request = normalize_request(
        {
            "links": ["https://example.com/a"],
            "notebook_name": "Audio Options",
            "output_path": str(output_path),
            "language": "fr",
            "audio_format": "debate",
            "audio_length": "long",
            "episode_focus": "Focus on disagreements.",
        }
    )

    result = asyncio.run(generate_audio_overview(request, adapter=adapter))

    assert result.ok is True
    assert result.artifact is not None
    assert result.artifact.id == "art_3"
    assert result.artifact.status == "completed"
    assert result.artifact.title == "Focused Audio"
    assert result.output_path == output_path
    assert (
        "generate_audio",
        "nb_created_1",
        ("src_a",),
        "fr",
        "Focus on disagreements.",
        "debate",
        "long",
    ) in adapter.calls
    assert ("download_audio", "nb_created_1", "art_3", output_path) in adapter.calls


def test_generation_failure_is_reported_without_download(tmp_path: Path) -> None:
    adapter = FakeAdapter(
        add_sequences={
            "https://example.com/a": [
                AdapterSource(id="src_a", status="processing", url="https://example.com/a")
            ]
        },
        wait_results={
            "src_a": AdapterSource(id="src_a", status="ready", url="https://example.com/a")
        },
        generation_result=AdapterArtifact(id="art_4", status="in_progress", kind="audio"),
        completion_result=AdapterArtifact(
            id="art_4",
            status="failed",
            kind="audio",
            error="quota exceeded",
        ),
    )
    request = normalize_request(
        {
            "links": ["https://example.com/a"],
            "notebook_name": "Generation Failure",
            "output_path": str(tmp_path / "failure.mp3"),
        }
    )

    result = asyncio.run(generate_audio_overview(request, adapter=adapter))

    assert result.ok is False
    assert [error.code for error in result.errors] == ["audio_generation_failed"]
    assert all(call[0] != "download_audio" for call in adapter.calls)


def test_fails_when_no_sources_become_ready(tmp_path: Path) -> None:
    adapter = FakeAdapter(
        add_sequences={
            "https://example.com/a": [
                AdapterSource(id="src_a", status="processing", url="https://example.com/a")
            ]
        },
        wait_results={"src_a": TimeoutError("source wait timed out")},
    )
    request = normalize_request(
        {
            "links": ["https://example.com/a"],
            "notebook_name": "No Ready Sources",
            "output_path": str(tmp_path / "none.mp3"),
        }
    )

    result = asyncio.run(generate_audio_overview(request, adapter=adapter))

    assert result.ok is False
    assert [error.code for error in result.errors] == ["no_sources_ready"]
    assert result.sources[0].status == "timeout"
