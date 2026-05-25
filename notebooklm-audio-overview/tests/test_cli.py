import io
import json
from pathlib import Path

from skills.notebooklm_audio_overview import (
    RunError,
    create_result,
    normalize_request,
)
from skills.notebooklm_audio_overview import cli


def _write_request(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_cli_reads_request_from_input_file_and_prints_success_json(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    request_path = tmp_path / "request.json"
    _write_request(
        request_path,
        {
            "links": ["https://example.com/article"],
            "notebook_name": "Research Briefing",
            "output_path": str(tmp_path / "briefing.mp3"),
        },
    )

    captured_payload: dict[str, object] = {}

    def fake_run(payload: dict[str, object]):
        captured_payload.update(payload)
        request = normalize_request(payload)
        return create_result(request, ok=True)

    monkeypatch.setattr(cli, "generate_audio_overview_from_links", fake_run)

    exit_code = cli.main(["--input", str(request_path)])
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert captured_payload["notebook_name"] == "Research Briefing"
    assert json.loads(stdout)["ok"] is True


def test_cli_reads_request_from_stdin(tmp_path: Path, monkeypatch, capsys) -> None:
    payload = {
        "links": ["https://example.com/article"],
        "notebook_name": "Stdin Briefing",
        "output_path": str(tmp_path / "stdin.mp3"),
    }

    def fake_run(raw_payload: dict[str, object]):
        request = normalize_request(raw_payload)
        return create_result(request, ok=True)

    monkeypatch.setattr(cli, "generate_audio_overview_from_links", fake_run)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))

    exit_code = cli.main(["--stdin"])
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert json.loads(stdout)["ok"] is True


def test_cli_returns_structured_validation_failure_for_bad_payload(
    tmp_path: Path,
    capsys,
) -> None:
    request_path = tmp_path / "bad-request.json"
    _write_request(
        request_path,
        {
            "links": [],
            "notebook_name": "Research Briefing",
        },
    )

    exit_code = cli.main(["--input", str(request_path)])
    stdout = capsys.readouterr().out
    payload = json.loads(stdout)

    assert exit_code == 2
    assert payload["ok"] is False
    assert payload["output_path"] is None
    assert payload["errors"][0]["code"] == "missing_links"


def test_cli_returns_non_zero_when_orchestration_reports_failure(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    request_path = tmp_path / "request.json"
    _write_request(
        request_path,
        {
            "links": ["https://example.com/article"],
            "notebook_name": "Failure Briefing",
            "output_path": str(tmp_path / "failure.mp3"),
        },
    )

    def fake_run(payload: dict[str, object]):
        request = normalize_request(payload)
        return create_result(
            request,
            ok=False,
            errors=[RunError(code="audio_generation_failed", message="boom", target="artifact")],
        )

    monkeypatch.setattr(cli, "generate_audio_overview_from_links", fake_run)

    exit_code = cli.main(["--input", str(request_path)])
    stdout = capsys.readouterr().out
    payload = json.loads(stdout)

    assert exit_code == 1
    assert payload["ok"] is False
    assert payload["errors"][0]["code"] == "audio_generation_failed"


def test_cli_returns_structured_json_for_invalid_json_input(tmp_path: Path, capsys) -> None:
    request_path = tmp_path / "bad-json.json"
    request_path.write_text("{not-json", encoding="utf-8")

    exit_code = cli.main(["--input", str(request_path)])
    stdout = capsys.readouterr().out
    payload = json.loads(stdout)

    assert exit_code == 2
    assert payload["ok"] is False
    assert payload["errors"][0]["code"] == "invalid_json"


def test_cli_returns_structured_json_for_invalid_cli_args(capsys) -> None:
    exit_code = cli.main([])
    stdout = capsys.readouterr().out
    payload = json.loads(stdout)

    assert exit_code == 2
    assert payload["ok"] is False
    assert payload["errors"][0]["code"] == "invalid_cli_args"
