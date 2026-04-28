# Setup Project Worklog Reference

Use these as starter templates. Adapt them to each repository instead of forcing exact wording.

## `AGENTS.md`

- Put the `## Worklog` section first by default so it is loaded early in new sessions.
- Keep it focused on durable workflow rules, not active task state.
- Store active state in `notes/worklog/INDEX.md` and feature notes.
- Store substantial plans in `notes/plans/<feature-slug>.md` and link them from the feature note.
- Use the full current baseline structure, not only the worklog section, when initializing a new repo.

## How to prompt the skill

What to include about the feature:

- short feature name
- goal
- current status
- next steps if known
- blockers if any

Example prompt:

```text
Load and follow the setup-project-worklog skill. Set up this repo with the first-version AGENTS.md and worklog structure, and create or update a feature note for "<feature name>".

Goal: <what success looks like>
Status: <current state>
Next: <next steps>
Blockers: <blockers, if any>
```

If the repo is already set up, shorten the request to just creating or updating the feature note.
If the work needs a substantial plan, mention that too so the skill can create or update `notes/plans/<feature-slug>.md`.

## `notes/worklog/INDEX.md`

```md
# Worklog Index

## Active

- `notes/worklog/<feature-slug>.md` - one-line status

## Blocked

- `notes/worklog/<feature-slug>.md` - blocker

## Paused

- `notes/worklog/<feature-slug>.md` - reason

## Recently Completed

- `notes/worklog/<feature-slug>.md` - completed YYYY-MM-DD
```

## `notes/worklog/templates/FEATURE.md`

```md
# <Feature Name>

## Goal

<what success looks like>

## Status

<current state in 2-4 lines>

## Next

- ...
- ...
- ...

## Decisions

- ...

## Verification

- Status: <not run / in progress / verified / partial>
- Evidence: <tests, logs, diffs, runtime checks>

## Lessons Learned

- Promote reusable repo-wide lessons to `notes/worklog/LESSONS.md`.
- Record task-specific lessons here until they are stable enough to share repo-wide.

## Plan

- Summary: ...
- Detailed plan: `notes/plans/<feature-slug>.md`

## References

- Branch: `<branch-name>`
- PR: `#...`
- Commit: `<sha>`
- Files: `src/...`
- Issue: `...`
- Test: `npm test -- ...`

## Resume

- Open `...`
- Run `...`
- Verify `...`
```

## `notes/worklog/LESSONS.md`

```md
# Repo Lessons

## Verification

- Prefer `docker exec trip-service-ui ...` or `./docker_env.sh up` for test runs when local Node dependencies are flaky.
```

## Example Feature Slugs

- `auth-oauth-cleanup`
- `billing-webhook-retry`
- `mobile-nav-polish`

## `notes/plans/<feature-slug>.md`

Use this file when planning is more than a few bullets, likely to evolve, or involves architecture, risk, migration, or investigation.

Suggested shape:

```md
# <Feature Name> Plan

## Goal

...

## Scope

- ...

## Assumptions

- ...

## Plan

- ...

## Verification

- ...

## Risks

- ...
```

## Archive Rule

- Keep active and paused work in `notes/worklog/`
- Move completed, cancelled, or stale feature notes to `notes/worklog/archive/`
- Leave only a short recent-completion pointer in `notes/worklog/INDEX.md`

## Full `AGENTS.md` baseline

Use this baseline when initializing a repo, adapting wording only when the target repo already has clearly equivalent instructions:

```md
# Agent Working Rules

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
