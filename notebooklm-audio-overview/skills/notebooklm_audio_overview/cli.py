"""Command-line entrypoint for the NotebookLM audio overview skill."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .models import RequestValidationError, RunError
from .skill import generate_audio_overview_from_links

EXIT_SUCCESS = 0
EXIT_RUNTIME_FAILURE = 1
EXIT_INPUT_FAILURE = 2


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and emit a stable JSON result to stdout."""

    try:
        args = _build_parser().parse_args(argv)
        payload = _load_payload(args)
    except RequestValidationError as exc:
        _print_json(_failure_payload(exc.code, exc.message, exc.target))
        return EXIT_INPUT_FAILURE

    try:
        result = generate_audio_overview_from_links(payload)
    except RequestValidationError as exc:
        _print_json(_failure_payload(exc.code, exc.message, exc.target))
        return EXIT_INPUT_FAILURE
    except Exception as exc:
        _print_json(_failure_payload("cli_runtime_error", str(exc), None))
        return EXIT_RUNTIME_FAILURE

    _print_json(result.to_dict())
    return EXIT_SUCCESS if result.ok else EXIT_RUNTIME_FAILURE


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog="notebooklm-audio-overview",
        description="Generate a NotebookLM audio overview from a JSON request.",
    )
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument(
        "--input",
        type=Path,
        help="Path to a JSON request file.",
    )
    inputs.add_argument(
        "--stdin",
        action="store_true",
        help="Read the JSON request payload from stdin.",
    )
    return parser


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise RequestValidationError(
            code="invalid_cli_args",
            message=message,
            target="cli",
        )


def _load_payload(args: argparse.Namespace) -> Mapping[str, Any]:
    if args.input is not None:
        raw_text = _read_input_file(args.input)
    else:
        raw_text = sys.stdin.read()

    if not raw_text.strip():
        raise RequestValidationError(
            code="empty_input",
            message="Request input was empty.",
            target="request",
        )

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise RequestValidationError(
            code="invalid_json",
            message=f"Request input is not valid JSON: {exc.msg}",
            target="request",
        ) from exc

    if not isinstance(payload, Mapping):
        raise RequestValidationError(
            code="invalid_request",
            message="Request payload must be a JSON object.",
            target="request",
        )
    return payload


def _read_input_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RequestValidationError(
            code="input_not_found",
            message=f"Input file was not found: {path}",
            target="input",
        ) from exc
    except OSError as exc:
        raise RequestValidationError(
            code="input_read_failed",
            message=f"Could not read input file {path}: {exc}",
            target="input",
        ) from exc


def _failure_payload(code: str, message: str, target: str | None) -> dict[str, Any]:
    return {
        "ok": False,
        "notebook": None,
        "sources": [],
        "artifact": None,
        "output_path": None,
        "warnings": [],
        "errors": [
            RunError(
                code=code,
                message=message,
                target=target,
            ).to_dict()
        ],
    }


def _print_json(payload: Mapping[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
