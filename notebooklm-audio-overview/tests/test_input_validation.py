from pathlib import Path

import pytest

from skills.notebooklm_audio_overview import RequestValidationError, normalize_request


def test_rejects_empty_links() -> None:
    with pytest.raises(RequestValidationError) as exc_info:
        normalize_request({"links": [], "notebook_name": "Research Briefing"})

    assert exc_info.value.code == "missing_links"


@pytest.mark.parametrize(
    ("payload", "target"),
    [
        ({"links": ["ftp://example.com"], "notebook_name": "Briefing"}, "links"),
        ({"links": ["https://example.com"], "notebook_name": ""}, "notebook_name"),
        (
            {"links": ["https://example.com"], "notebook_name": "Briefing", "audio_format": "epic"},
            "audio_format",
        ),
        (
            {"links": ["https://example.com"], "notebook_name": "Briefing", "audio_length": "tiny"},
            "audio_length",
        ),
    ],
)
def test_rejects_invalid_payload_values(payload: dict[str, object], target: str) -> None:
    with pytest.raises(RequestValidationError) as exc_info:
        normalize_request(payload)

    assert exc_info.value.target == target


def test_applies_defaults_and_resolves_output_path() -> None:
    request = normalize_request(
        {
            "links": ["https://example.com/article"],
            "notebook_name": "Research Briefing",
        }
    )

    assert request.language == "en"
    assert request.audio_format is None
    assert request.audio_length is None
    assert request.timeout_seconds == 300
    assert request.source_timeout_seconds == 300
    assert request.audio_timeout_seconds == 300
    assert request.poll_interval_seconds == 2.0
    assert request.output_path.is_absolute()
    assert request.output_path == (Path.cwd() / "output" / "research-briefing.mp3").resolve()


def test_uses_legacy_timeout_as_fallback_for_source_and_audio_timeouts() -> None:
    request = normalize_request(
        {
            "links": ["https://example.com/article"],
            "notebook_name": "Research Briefing",
            "timeout_seconds": 480,
        }
    )

    assert request.timeout_seconds == 480
    assert request.source_timeout_seconds == 480
    assert request.audio_timeout_seconds == 480


def test_accepts_explicit_source_and_audio_timeouts() -> None:
    request = normalize_request(
        {
            "links": ["https://example.com/article"],
            "notebook_name": "Research Briefing",
            "timeout_seconds": 300,
            "source_timeout_seconds": 120,
            "audio_timeout_seconds": 900,
        }
    )

    assert request.timeout_seconds == 300
    assert request.source_timeout_seconds == 120
    assert request.audio_timeout_seconds == 900


def test_accepts_resume_request_without_links() -> None:
    request = normalize_request(
        {
            "resume_notebook_id": "nb_resume",
            "resume_artifact_id": "art_resume",
            "output_path": "output/resume.mp3",
        }
    )

    assert request.links == ()
    assert request.resume_notebook_id == "nb_resume"
    assert request.resume_artifact_id == "art_resume"
    assert request.output_path.is_absolute()


@pytest.mark.parametrize(
    "payload",
    [
        {
            "resume_artifact_id": "art_resume",
            "output_path": "output/resume.mp3",
        },
        {
            "resume_notebook_id": "nb_resume",
            "output_path": "output/resume.mp3",
        },
    ],
)
def test_requires_both_resume_identifiers(payload: dict[str, object]) -> None:
    with pytest.raises(RequestValidationError) as exc_info:
        normalize_request(payload)

    assert exc_info.value.code in {
        "missing_resume_notebook_id",
        "missing_resume_artifact_id",
    }
