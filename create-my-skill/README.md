# create-my-skill

Create a new skill and matching command wrapper in the user's home or repository `.agents` directories.

Use this when you want an agent to scaffold a skill in the consolidated layout:

- `~/.agents/skills/<skill-name>/SKILL.md`
- `~/.agents/commands/<skill-name>.md`
- `<repo>/.agents/skills/<skill-name>/SKILL.md`
- `<repo>/.agents/commands/<skill-name>.md`

The skill keeps `SKILL.md` as the source of truth and creates command files as thin wrappers only.
