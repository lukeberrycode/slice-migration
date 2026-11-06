---
description: Set up a project for a slice migration or a new design - the gate config and the Discovery templates
argument-hint: "[path to the legacy slice] | --design"
allowed-tools: [Bash, Read, Write, Glob]
---

# Set up a slice migration or a new design

Prepare this project using the method in `${CLAUDE_PLUGIN_ROOT}/method.md`. Discovery has two sources, and the arguments say which: `$ARGUMENTS`

1. **Choose the source.**
   - `--design`: **from a new design.** There's no old slice, or it isn't the authority on what the product should do.
   - A path: **from the old slice** at that path.
   - Neither: ask which source this project has. For the old slice, also ask for its path, suggesting `legacy`.
   - Both: stop. Discovery from both sources at once isn't supported yet, so ask the person to choose one.

   **From the old slice only:** if the path doesn't exist, ask where the old slice's code is. Don't copy, move or change it.
2. **Write the config** to `.claude/slice-migration.json`. If that file already exists, don't change it. If it's for the other source (one source has a `legacy_path` and the other doesn't), or for a different old slice, stop here without copying anything: tell the person how it differs from the config for the chosen source, and let them decide. Replacing it could remove the protection on an old slice, and templates for the wrong source would leave the project mixed. If it's for the same source, keep it and go on.
   - From the old slice: start from `${CLAUDE_PLUGIN_ROOT}/templates/config.json`, with `legacy_path` set to the slice's path.
   - From a new design: copy `${CLAUDE_PLUGIN_ROOT}/templates/config-design.json`, leaving `legacy_path` empty.

   If the project already has a different layout (for example new code under `app/` not `src/`), adjust each phase's `paths`, and tell the person what you changed. Phases are matched in order, so a path in an earlier phase wins.
3. **Copy the Discovery templates** to `docs/discovery/`, all in that one folder, so a project's layout doesn't depend on its source. Never overwrite a file that's already there; list any you skipped.
   - The shared ones, for both sources: `${CLAUDE_PLUGIN_ROOT}/templates/discovery/*.md`.
   - From the old slice: `${CLAUDE_PLUGIN_ROOT}/templates/discovery/legacy/*.md`.
   - From a new design: `${CLAUDE_PLUGIN_ROOT}/templates/discovery/design/*.md`.
4. **Remove what doesn't apply,** only in the files you just copied. Leave any file that was already there as it is.
   - From the old slice: in `README.md`, delete "Questions: from a new design" and "Checklist: from a new design".
   - From a new design: in `README.md`, delete "Questions: from the old slice" and "Checklist: from the old slice". In `requirements.md`, delete "Features in the manual, and their requirements".
   - For either: in `README.md`, delete the sentence that says the file covers both sources.
5. **Don't create the gates file** (`docs/gates.json` by default). Only a person writes it, and the gate hook will block you.
6. **Report back:** the source, what was created, the phases and their paths, and that a person approves each gate by adding `"<phase>": {"approved_by": "<name>", "date": "<YYYY-MM-DD>"}` to the gates file. Then say how to start Discovery:
   - From the old slice: with the `discovery` skill.
   - From a new design: by following "From a new design" under Discovery in the method's Generic timeline.
