---
name: setup-project-worklog
description: Initialize a reusable project operating baseline with AGENTS.md rules, worklog files, feature note templates, and plan/archive structure. Use when a user wants resumable task tracking across sessions, standardized repo instructions, session notes, feature worklogs, or repo work-in-progress templates.
---

# Setup Project Worklog

Set up a small, durable project operating baseline for a repository.

Default first version:

- `AGENTS.md` contains the full reusable agent working baseline from the source repo, adapted to the target repo as needed
- `notes/worklog/INDEX.md` tracks active, blocked, paused, and recently completed work
- `notes/worklog/LESSONS.md` stores reusable repo-wide lessons that every session should read
- `notes/worklog/templates/FEATURE.md` is the reusable feature note template
- `notes/plans/<feature-slug>.md` stores longer-form plans when needed
- `notes/worklog/archive/` stores completed or stale feature notes

## When To Use

Use this skill when the user wants to:

- persist work between chat sessions
- initialize a repo with a reusable `AGENTS.md` baseline
- keep feature-specific progress notes without bloating `AGENTS.md`
- standardize `AGENTS.md`, `INDEX.md`, and feature note templates across repos
- add a resumable worklog workflow to a project

## Workflow

1. Inspect the repo for `AGENTS.md`, existing worklog files, and any similar notes structure.
2. Default to the first-version layout above unless the user gives a different structure.
3. Create or update these repo files:
   - `AGENTS.md`
   - `notes/worklog/INDEX.md`
   - `notes/worklog/LESSONS.md`
   - `notes/worklog/templates/FEATURE.md`
   - `notes/plans/` if missing
   - `notes/worklog/archive/` if missing
4. When creating or updating `AGENTS.md`, use the full reusable baseline from the source repo, not just the worklog section. Preserve equivalent repo-specific instructions when they already exist.
5. Keep `AGENTS.md` concise. Put the `## 1. Worklog` section first, before other numbered workflow rules, unless the repo already has a stronger top-level convention.
6. Keep `INDEX.md` small and scannable with these sections:
   - `## Active`
   - `## Blocked`
   - `## Paused`
   - `## Recently Completed`
7. Ensure the full `AGENTS.md` baseline covers these rule areas:
   - worklog usage, file layout, and tracking default (track everything, exempt fire-and-forget ops)
   - progress check on every response
   - planning before non-trivial work
   - execution: root-cause fixes, verification, proactive diagnosis
8. Put durable resume context in feature notes only:
   - goal
   - status
   - next steps
   - decisions
   - verification
   - task-specific lessons learned
   - plan link when a separate plan exists
   - references
   - resume steps
9. Store repo-wide reusable lessons in `notes/worklog/LESSONS.md`, not `AGENTS.md`. Keep it short and worth reading every session.
10. For any non-trivial task, start with a short plan. If the plan is more than a few bullets or likely to evolve, create or update `notes/plans/<feature-slug>.md` and link it from the feature note.
11. Do not store noisy command output, scratch notes, or broad multi-feature logs.
12. If the repo already has a similar system, adapt to it instead of duplicating structures.
13. Validate the result:
    - `AGENTS.md` contains the full baseline rule set adapted for the target repo
    - `AGENTS.md` contains a `## 1. Worklog` section near the top
    - `notes/worklog/INDEX.md` exists
    - `notes/worklog/LESSONS.md` exists
    - `notes/worklog/templates/FEATURE.md` exists
    - `notes/plans/` exists
    - no duplicate parallel tracking structure was introduced

## Prompting Guide

If the user asks how to prompt this skill for the feature they are working on, give them a concise template and ask for only the durable context needed to bootstrap or update a feature note.

What to include about the feature:

- short feature name
- goal
- current status
- next steps if known
- blockers if any

If the work is non-trivial, the user can also include planning context such as assumptions, constraints, or a request to create a detailed plan note.

Use a concise template like this:

```text
Load and follow the setup-project-worklog skill. <set up this repo with the first-version AGENTS.md and worklog structure / create or update the worklog for this repo>, and create or update a feature note for "<feature name>".

Goal: <what success looks like>
Status: <current state>
Next: <next steps>
Blockers: <blockers, if any>
```

If the repo is already set up, prefer a shorter variant focused on the feature note update.
If the work needs a longer plan, create or update `notes/plans/<feature-slug>.md` and keep only a short summary in the feature note.

## AGENTS.md Rules To Add

Use this full baseline pattern, adapted to the repo's tone and existing instructions. Place it at the top of `AGENTS.md` by default:

```md
## 1. Worklog

Persist resumable context across sessions. **Track every task by default** — only skip fire-and-forget ops (launching runs, starting servers, verbatim one-off commands, pure Q&A).

### Files

| Purpose | Path |
|---|---|
| Active index | `notes/worklog/INDEX.md` |
| Repo lessons | `notes/worklog/LESSONS.md` |
| Feature notes | `notes/worklog/<feature-slug>.md` |
| Template | `notes/worklog/templates/FEATURE.md` |
| Plans | `notes/plans/<feature-slug>.md` |
| Archive | `notes/worklog/archive/` |

### Session start

- Read `notes/worklog/INDEX.md` and `notes/worklog/LESSONS.md`. Open only the relevant feature note.

### Creating and updating notes

- No note for this task? Create one from the template.
- Continuing existing work? Update the existing note — don't create a new one.
- Update `INDEX.md` when status changes (active / paused / blocked / complete).
- Promote reusable repo-wide lessons to `notes/worklog/LESSONS.md`; keep task-specific lessons in the feature note.
- Record only: goal, status, next steps, key decisions, blockers, plan link, references.
- Keep verification evidence in the feature note instead of burying it inside status updates.
- Plans longer than a few bullets go in `notes/plans/<feature-slug>.md`, linked from the note.

### Progress check — every response

After completing each response, check: did status, findings, or next steps change? If yes, append a one-liner update to the feature note. If blocked or done, update `INDEX.md` too. Keep each update to 1-2 lines — no rewrites.

### Archiving

Move completed/cancelled/stale notes to `notes/worklog/archive/` and remove them from `INDEX.md`.

### Content rules

- One-liners and bullet lists. No verbose output, scratch work, or duplicated code.
- One note per task. Update, don't proliferate.
- Keep `notes/worklog/LESSONS.md` short and reusable; record only lessons likely to matter in future sessions.
- `AGENTS.md` stays static — no session-specific state here.

## 2. Planning

- Start non-trivial tasks with a short plan. Make assumptions explicit.
- If the plan grows, persist it in `notes/plans/<feature-slug>.md`.
- If evidence contradicts the plan, stop, re-plan, and update the notes.

## 3. Execution

- Fix root causes, not symptoms. Keep changes small and local.
- Verify before marking done — tests, logs, diffs, or runtime checks.
- If verification is incomplete, state what remains and why.
- Diagnose bugs proactively; ask the user only when truly blocked.
```

## Reference

For starter templates and example file bodies, read [reference.md](reference.md).

## Output

When done, report:

- which files were created or updated
- whether an existing worklog system was reused or adapted
- any assumptions made
- how the repo should use the worklog going forward
