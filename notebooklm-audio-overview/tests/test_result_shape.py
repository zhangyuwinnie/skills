from pathlib import Path

from skills.notebooklm_audio_overview import (
    ArtifactResult,
    NotebookResult,
    RunWarning,
    SourceResult,
    create_result,
    normalize_request,
)


def test_output_path_collision_creates_timestamped_sibling(tmp_path: Path) -> None:
    existing = tmp_path / "briefing.mp3"
    existing.write_text("existing audio")

    request = normalize_request(
        {
            "links": ["https://example.com/article"],
            "notebook_name": "Research Briefing",
            "output_path": str(existing),
        }
    )

    assert request.output_path.parent == existing.parent.resolve()
    assert request.output_path != existing.resolve()
    assert request.output_path.suffix == ".mp3"
    assert request.output_path.name.startswith("briefing-")


def test_overwrite_true_keeps_requested_output_path(tmp_path: Path) -> None:
    existing = tmp_path / "briefing.mp3"
    existing.write_text("existing audio")

    request = normalize_request(
        {
            "links": ["https://example.com/article"],
            "notebook_name": "Research Briefing",
            "output_path": str(existing),
            "overwrite": True,
        }
    )

    assert request.output_path == existing.resolve()


def test_result_serialization_keeps_stable_shape(tmp_path: Path) -> None:
    output_path = tmp_path / "briefing.mp3"
    request = normalize_request(
        {
            "links": ["https://example.com/article"],
            "notebook_name": "Research Briefing",
            "output_path": str(output_path),
        }
    )

    result = create_result(
        request,
        ok=True,
        notebook=NotebookResult(id="nb_123", title="Research Briefing", reused=False),
        sources=[
            SourceResult(
                input_url="https://example.com/article",
                normalized_url="https://example.com/article",
                source_id="src_123",
                title="Example Article",
                kind="web_page",
                status="ready",
                ready=True,
            )
        ],
        artifact=ArtifactResult(
            id="art_123",
            kind="audio",
            status="completed",
            title="Audio Overview",
        ),
        warnings=[RunWarning(code="partial_source_failure", message="One source failed.")],
    )

    payload = result.to_dict()

    assert payload == {
        "ok": True,
        "notebook": {
            "id": "nb_123",
            "title": "Research Briefing",
            "reused": False,
        },
        "sources": [
            {
                "input_url": "https://example.com/article",
                "normalized_url": "https://example.com/article",
                "source_id": "src_123",
                "title": "Example Article",
                "kind": "web_page",
                "status": "ready",
                "ready": True,
                "error": None,
            }
        ],
        "artifact": {
            "id": "art_123",
            "kind": "audio",
            "status": "completed",
            "title": "Audio Overview",
        },
        "output_path": str(output_path.resolve()),
        "warnings": [
            {
                "code": "partial_source_failure",
                "message": "One source failed.",
                "target": None,
            }
        ],
        "errors": [],
    }
