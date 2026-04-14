import json
import os
from pathlib import Path

import pytest

from skills.notebooklm_audio_overview import cli


def test_live_cli_smoke(tmp_path: Path, capsys) -> None:
    if os.getenv("NOTEBOOKLM_LIVE") != "1":
        pytest.skip("Set NOTEBOOKLM_LIVE=1 to enable the live NotebookLM smoke test.")

    raw_links = os.getenv("NOTEBOOKLM_TEST_LINKS", "").strip()
    if not raw_links:
        pytest.skip("Set NOTEBOOKLM_TEST_LINKS to a comma-separated list of live test URLs.")

    links = [value.strip() for value in raw_links.split(",") if value.strip()]
    if not links:
        pytest.skip("NOTEBOOKLM_TEST_LINKS did not contain any usable URLs.")

    request_path = tmp_path / "live-request.json"
    request_path.write_text(
        json.dumps(
            {
                "links": links,
                "notebook_name": "NotebookLM Audio Overview Live Smoke",
                "output_path": str(tmp_path / "live-smoke.mp3"),
                "reuse_notebook": False,
                "strict_mode": False,
                "timeout_seconds": 600,
                "source_timeout_seconds": 180,
                "audio_timeout_seconds": 900,
                "poll_interval_seconds": 3,
            }
        ),
        encoding="utf-8",
    )

    exit_code = cli.main(["--input", str(request_path)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert Path(payload["output_path"]).exists()
