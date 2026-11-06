---
description: Set up a project for a slice migration - the gate config and the Discovery templates
argument-hint: "[path to the legacy slice] (default: legacy)"
allowed-tools: [Bash, Read, Write, Glob]
---

# Set up a slice migration

Prepare this project to replace a legacy slice using the method in `${CLAUDE_PLUGIN_ROOT}/method.md`.

1. **Find the legacy slice.** Use `$ARGUMENTS` if given, otherwise `legacy`. If that path doesn't exist, ask where the old slice's code is. Don't copy, move or change it.
2. **Write the config** to `.claude/slice-migration.json`, starting from `${CLAUDE_PLUGIN_ROOT}/templates/config.json`, with `legacy_path` set to the slice's path. If the project already has a different layout (for example new code under `app/` not `src/`), adjust each phase's `paths`, and tell the person what you changed. Phases are matched in order, so a path in an earlier phase wins.
3. **Copy the Discovery templates** to `docs/discovery/`, all in that one folder: the shared ones from `${CLAUDE_PLUGIN_ROOT}/templates/discovery/*.md`, and the old slice's from `${CLAUDE_PLUGIN_ROOT}/templates/discovery/legacy/*.md`. In the copied `README.md`, keep the old slice's questions and checklist, and delete the new design's. Never overwrite a file that's already there; list any you skipped.
4. **Don't create the gates file** (`docs/gates.json` by default). Only a person writes it, and the gate hook will block you.
5. **Report back:** what was created, the phases and their paths, and that a person approves each gate by adding `"<phase>": {"approved_by": "<name>", "date": "<YYYY-MM-DD>"}` to the gates file. Then suggest starting Discovery with the `discovery` skill.
