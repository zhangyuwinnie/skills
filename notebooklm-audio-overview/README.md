# NotebookLM Audio Overview Skill

Thin local Python skill around `notebooklm-py` that turns a list of links into one downloaded NotebookLM Audio Overview and returns structured JSON.

## What It Does

- validates and normalizes a JSON request
- creates or reuses a NotebookLM notebook
- imports HTTP/HTTPS links as sources
- waits for source readiness
- generates one audio overview
- downloads the audio file locally
- prints stable JSON to stdout for both success and failure cases

## Requirements

- Python `3.10+`
- NotebookLM auth already completed with `notebooklm login`

## Install

Clone the repo, create a virtualenv, and install the package:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

For local development, editable install also works:

```bash
python -m pip install -e .[dev]
```

Then complete NotebookLM auth:

```bash
notebooklm login
```

The login step is browser-backed and must succeed before the installed CLI can talk to NotebookLM.

## OpenClaw Dev Loop

If you want OpenClaw to debug and modify this repo directly, use the repo-local workflow documented at [docs/openclaw-dev-workflow.md](/Users/yuzhang/Desktop/work/skills/notebookLM/docs/openclaw-dev-workflow.md).
That path keeps one source of truth, uses wrapper scripts that always target this repo's `.venv`, and is designed for a fast test-fix-rerun loop on branch `openclaw-dev`.

## Example Request

The repo includes an example payload at [skills/notebooklm_audio_overview/examples/example_input.json](/Users/yuzhang/Desktop/work/skills/notebookLM/skills/notebooklm_audio_overview/examples/example_input.json).
For a Chinese AI-news first-principles podcast briefing, use [skills/notebooklm_audio_overview/examples/example_ai_news_first_principles.json](/Users/yuzhang/Desktop/work/skills/notebookLM/skills/notebooklm_audio_overview/examples/example_ai_news_first_principles.json).
For resumable follow-up, use [skills/notebooklm_audio_overview/examples/example_resume_input.json](/Users/yuzhang/Desktop/work/skills/notebookLM/skills/notebooklm_audio_overview/examples/example_resume_input.json).

Core fields:

- `links`: non-empty list of HTTP/HTTPS URLs
- `notebook_name`: target notebook title
- `output_path`: destination `.mp3` path
- `reuse_notebook`: reuse the newest exact title match instead of always creating
- `strict_mode`: fail if any source does not become ready

Optional tuning fields:

- `language`
- `audio_format`: `deep-dive`, `brief`, `critique`, `debate`
- `audio_length`: `short`, `default`, `long`
- `episode_focus`
- `timeout_seconds`: legacy fallback used when the more specific timeout fields are omitted
- `source_timeout_seconds`: budget for source readiness waits
- `audio_timeout_seconds`: budget for audio generation waits
- `poll_interval_seconds`
- `overwrite`

Resume-only fields:

- `resume_notebook_id`: explicit notebook ID from a prior run result
- `resume_artifact_id`: explicit audio artifact ID from a prior run result

When both resume fields are present, the skill skips notebook creation, source import, and audio generation. It only waits for the existing artifact and downloads it.

## Run

From a JSON file:

```bash
notebooklm-audio-overview --input skills/notebooklm_audio_overview/examples/example_input.json
```

From stdin:

```bash
cat skills/notebooklm_audio_overview/examples/example_input.json | notebooklm-audio-overview --stdin
```

Run the AI-news first-principles podcast example:

```bash
notebooklm-audio-overview --input skills/notebooklm_audio_overview/examples/example_ai_news_first_principles.json
```

Resume an existing artifact:

```bash
notebooklm-audio-overview --input skills/notebooklm_audio_overview/examples/example_resume_input.json
```

Module invocation still works if you prefer not to install the console script:

```bash
.venv/bin/python -m skills.notebooklm_audio_overview.cli --input skills/notebooklm_audio_overview/examples/example_input.json
```

Exit codes:

- `0`: success
- `1`: execution reached NotebookLM but the run failed
- `2`: request loading, JSON parsing, or request validation failed

## Output Shape

The CLI always prints JSON to stdout with these top-level keys:

- `ok`
- `notebook`
- `sources`
- `artifact`
- `output_path`
- `warnings`
- `errors`

On validation or input-loading failures, the same shape is kept and `output_path` is `null`.

## Verification

Default local verification:

```bash
.venv/bin/python -m pytest
```

Installability check used in this repo:

```bash
.venv/bin/python -m pip install -e .
.venv/bin/notebooklm-audio-overview --help
```

Optional live smoke check:

```bash
NOTEBOOKLM_LIVE=1 \
NOTEBOOKLM_TEST_LINKS='https://example.com/article-one,https://example.com/article-two' \
.venv/bin/python -m pytest tests/test_live_integration.py -s
```

That live test stays skipped unless the environment is explicitly prepared.
It now uses a shorter source-processing timeout and a longer audio-generation timeout so slow audio jobs do not consume the entire source budget.
In this workspace, a narrower real run also succeeded with one public Wikipedia URL, `audio_format=brief`, and `audio_length=short`.
In this workspace, a more podcast-like real run also succeeded with one public Wikipedia URL, `audio_format=deep-dive`, `audio_length=default`, and an explicit conversational two-host instruction.

## Troubleshooting

`authentication_required`

- Run `.venv/bin/python -m notebooklm login`.
- Confirm the saved auth state belongs to the same user environment running the skill.

`no_sources_ready`

- One or more links may be blocked, unsupported, or still processing when the timeout expires.
- Increase `source_timeout_seconds` or retry with fewer links.

`audio_generation_failed`

- NotebookLM may reject the request because sources are not ready enough or generation failed server-side.
- Retry after checking the per-source statuses in the JSON result.
- The narrowest proven live profile in this workspace used one public URL with `audio_format=brief` and `audio_length=short`.
- A more podcast-like proven live profile in this workspace used one public URL with `audio_format=deep-dive`, `audio_length=default`, and explicit two-host conversational instructions.

`audio_generation_timeout`

- NotebookLM accepted the request but the audio artifact did not complete before the audio wait budget expired.
- Increase `audio_timeout_seconds` for long-running jobs and reuse the notebook inputs on the next run if needed.

Resume a pending artifact from a previous run

- Re-run the skill with `resume_notebook_id`, `resume_artifact_id`, and a fresh `output_path`.
- Use the `notebook.id` and `artifact.id` values returned by the earlier JSON result.

CLI returns `invalid_json` or `invalid_request`

- Make sure the input is a single JSON object, not a JSON array or partial fragment.

## Known Limits

- The default verification path still uses mocked NotebookLM operations unless you explicitly enable the live check.
- One-link live end-to-end success is now verified in this workspace for both a summary-like profile and a more podcast-like `deep-dive` profile, but broader multi-link live reliability is still service-dependent and not guaranteed by the default test suite.
- Automatic CLI fallback for missing Python API behavior is intentionally not implemented in v1.
- The tool currently targets one audio overview per request.
