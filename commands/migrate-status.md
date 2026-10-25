---
description: Show where a slice migration is - the current phase, which gates are approved, and what's waiting on a person
allowed-tools: [Read, Glob, Grep, Bash]
---

# Slice migration status

Read `.claude/slice-migration.json` and the gates file it names. If there's no config, say the project isn't set up and suggest `/slice-migration:migrate-init`.

Report, briefly:

1. **Gates:** for each phase in order, approved (by whom, when) or not.
2. **Current phase:** the first phase whose gate isn't approved. Work on later phases is blocked by the gate hook.
3. **Progress on the current phase.** For Discovery: the checklist in `docs/discovery/README.md`; the number of requirements in `docs/discovery/requirements.md` by status (Hypothesis, Confirmed, Corrected, By hand); requirements with no test (from `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/trace.py" .`); keep-or-fix entries without a decision; rows in `agent-errors.md`.
4. **Waiting on a person:** every decision that only a person can make.

Don't change any files.
