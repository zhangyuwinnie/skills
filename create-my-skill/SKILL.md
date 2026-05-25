---
name: create-my-skill
description: Create a new skill and matching command wrapper in the user's home or repository .agents directories. Use whenever the user wants to add a new skill, scaffold a command wrapper, update skill authoring guidance, or decide whether a skill should live globally or in a specific repo, even if they do not explicitly name this skill.
---

# Create My Skill

Create new skills using the consolidated layout:

- Home-global skill: `~/.agents/skills/<skill-name>/SKILL.md`
- Home-global command: `~/.agents/commands/<skill-name>.md`
- Repo-local skill: `<repo>/.agents/skills/<skill-name>/SKILL.md`
- Repo-local command: `<repo>/.agents/commands/<skill-name>.md`

Keep `skills` as the workflow source of truth and `commands` as thin wrappers only.

## SKILL.md Format Reference

Every skill must have:

- **YAML frontmatter** with two required fields:
  - `name` - lowercase, hyphenated, matches the directory name
  - `description` - explains what the skill does AND when to trigger it. Make the trigger language "pushy" because skills under-trigger by default. Prefer phrasing like "Use whenever the user mentions X, Y, or Z, even if they do not explicitly ask for it."
- **A markdown body** with practical, actionable instructions. Prefer numbered steps and concrete commands over prose explanations.
- **Optional bundled resources** in subdirectories.

Folder layout:

```text
<skill-name>/
|-- SKILL.md          (required)
|-- scripts/          (optional - executable code for deterministic tasks)
|-- references/       (optional - docs loaded into context on demand)
`-- assets/           (optional - templates, icons, fonts)
```

Authoring rules:

- Write only to the canonical `.agents/` location. Do not write to tool-specific directories like `~/.cursor/skills-cursor/` or `~/.claude/skills/`; those should be symlinks or managed by `npx skills`.
- Do not duplicate content across tool-specific directories.
- Follow the existing wrapper pattern already used in `~/.agents/commands/*.md`
- Keep `SKILL.md` under ~500 lines. For longer content, move detail into `references/` and reference it from `SKILL.md`.

## Step 1: Determine Scope

Ask the user exactly one scope question if the target location is not already explicit:

- `home` - create a globally reusable skill
- `repo` - create a repo-local skill for the current repository

If AskUserQuestion is available, use it. Recommend `home` when the workflow is reusable across repos; recommend `repo` when it depends on repo structure, repo scripts, or repo conventions.

If the user chooses `repo`, also determine the repo root before writing files.

## Step 2: Gather Minimal Inputs

Collect or infer:

- skill name
- short purpose
- whether it should include extra reference files or scripts

Normalize the skill name to lowercase hyphenated form.

## Step 3: Choose Paths

### Home

- Skill dir: `~/.agents/skills/<skill-name>/`
- Skill file: `~/.agents/skills/<skill-name>/SKILL.md`
- Command file: `~/.agents/commands/<skill-name>.md`

### Repo

- Skill dir: `<repo>/.agents/skills/<skill-name>/`
- Skill file: `<repo>/.agents/skills/<skill-name>/SKILL.md`
- Command file: `<repo>/.agents/commands/<skill-name>.md`

Create missing parent directories if needed.

## Step 4: Write the Skill

Write a concise `SKILL.md` with frontmatter and practical instructions.

Minimum structure:

```markdown
---
name: <skill-name>
description: <what it does and when to use it - make the trigger language pushy>
---

# <Title>

## When To Use

- ...

## Workflow

1. ...

## Output

- ...
```

Guidelines:

- Keep it concise unless the workflow genuinely needs detail
- Prefer actionable steps over explanation
- Put reusable logic in the skill, not the command wrapper
- Preserve single source of truth

## Step 5: Write the Command Wrapper

Create a same-name wrapper using this format:

```md
---
description: Run the <skill-name> workflow
---

Load and follow the `<skill-name>` skill.

If arguments were provided, treat them as additional context:

$ARGUMENTS
```

Do not duplicate the skill body in the command file.

## Step 6: Validate

After writing files, verify:

- the skill file exists in the chosen `.agents/skills` path
- the same-name command exists in the chosen `.agents/commands` path
- the command is only a thin wrapper
- the skill name matches between directory, frontmatter, and command filename

## Decision Rule

Use `home` when the workflow is reusable across repositories.

Use `repo` when the workflow is tied to:

- repo-specific paths
- repo-specific test/build commands
- repo-specific standing conventions
- repo-specific architecture or deployment context

## Output Back To User

When done, report:

- scope chosen: `home` or `repo`
- skill path created
- command path created
- any follow-up files created
