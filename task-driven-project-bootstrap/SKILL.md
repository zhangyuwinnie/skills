---
name: task-driven-project-bootstrap
description: Create a task-driven project operating system for a new or existing software repo. Use when the user wants reusable setup for AGENTS.md, PROGRESS.md, tasks.md, continue-task execution, task planning, verification, and session handoff across projects.
---

# Task-Driven Project Bootstrap

Use this skill when a user wants to:

- set up `AGENTS.md`, `PROGRESS.md`, and `tasks.md` together
- make `continue task` work predictably across sessions
- standardize task execution, verification, and handoff rules
- reuse a stronger engineering workflow across repos

Do not use this skill when the user only wants lightweight progress tracking. For that, use `project-tracking-bootstrap`.

## What This Skill Produces

- `AGENTS.md`
  - session-start rules
  - continue-task behavior
  - task execution protocol
  - verification and handoff rules
- `PROGRESS.md`
  - current status
  - locked decisions
  - current batch
  - verification log
  - update rule
- `tasks.md`
  - batch-based task plan
  - small tasks
  - dependencies
  - acceptance criteria
  - stop points

## Preferred Workflow

1. Identify the target project directory.
2. Gather or infer:
   - project name
   - plan path
   - product thesis
   - dev command
   - verification command
   - optional E2E command
   - optional review command
   - initial next batch
3. Run the bundled bootstrap script:

```bash
bash skills/task-driven-project-bootstrap/scripts/bootstrap_task_driven_project.sh TARGET_DIR \
  --project-name "Project Name" \
  --plan-path "plans/mvp.md" \
  --progress-file "PROGRESS.md" \
  --tasks-file "tasks.md" \
  --dev-command "pnpm dev" \
  --build-command "pnpm build" \
  --e2e-command "pnpm exec playwright test" \
  --review-command "use review skill or manual review" \
  --thesis "One-line product thesis." \
  --next-batch "Highest-priority next implementation batch."
```

4. If the target repo already has any of these files, do not overwrite blindly.
5. After creation, read the generated files and adapt them to the real repo state.

## Guidance

- Prefer `PROGRESS.md` unless the repo already has an established lowercase convention.
- Keep `tasks.md` concrete. Each task should be small enough to complete in one focused batch.
- Keep the AGENTS protocol strict enough that a new session can resume work without extra prompting.
- Use this skill when the user wants execution discipline, not just documentation scaffolding.

## Bundled Resources

- Bootstrap script:
  - `skills/task-driven-project-bootstrap/scripts/bootstrap_task_driven_project.sh`
- Templates:
  - `skills/task-driven-project-bootstrap/templates/AGENTS.md.tpl`
  - `skills/task-driven-project-bootstrap/templates/PROGRESS.md.tpl`
  - `skills/task-driven-project-bootstrap/templates/tasks.md.tpl`
