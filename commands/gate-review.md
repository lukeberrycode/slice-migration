---
description: Have the read-only gate-reviewer agent check a phase before a person decides its gate, and save its report
argument-hint: "[phase] (default: the current phase)"
allowed-tools: [Read, Glob, Grep, Bash, Write, Agent]
---

# Gate review

1. **Find the phase.** Use `$ARGUMENTS` if given. Otherwise read `.claude/slice-migration.json` and the gates file, and take the first phase whose gate isn't approved.
2. **Run the trace check** for Discovery and later phases: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/trace.py" .`. Keep its output.
3. **Launch the `gate-reviewer` agent.** Tell it the phase, today's date, the files to review (Discovery: `docs/discovery/` and `tests/characterisation/`; stack: the RFC, its spikes and `docs/planning/architecture.md`; planning: the rest of `docs/planning/`), and the trace check's output in full. Also give it a list of every file in the project, excluding `.git` and dependency folders (for example from `git ls-files`), and of the legacy slice's files: in some Claude Code builds Glob and Grep aren't available, and the reviewer can only read files it knows the names of.
4. **Save its report**, unchanged, to `docs/reviews/<phase>-gate-<YYYY-MM-DD>.md`. If that file exists, add `-2`, `-3` and so on. `docs/reviews/` belongs to no phase, so the gate hook allows it at any gate.
5. **Report to the person:** the number of findings by severity, the High ones in a line each, and the report's path.

Don't fix findings unless the person asks. Never approve the gate, and never say it should pass: the review is evidence for the person's decision.
