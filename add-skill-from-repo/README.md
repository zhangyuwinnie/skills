# add-skill-from-repo

Import third-party skill repositories into the home agent system.

This skill clones external repositories into `~/.agents/vendor`, selects the upstream skills to expose, symlinks or copies them into `~/.agents/skills`, and creates matching thin command wrappers in `~/.agents/commands`.

Use it when you want to bring external skills into your local canonical skill layout without making the upstream repository itself the public interface.
