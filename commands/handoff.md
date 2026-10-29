---
description: Check that Discovery's output meets the Discovery handoff in the method - what Planning and later phases start from
argument-hint: "[--before-sign-off]"
allowed-tools: [Bash, Read]
---

# Handoff check

Run:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/handoff.py" $ARGUMENTS .
```

Use `--before-sign-off` while Discovery is still being prepared for its gate: it skips the check that a person has approved the gate.

Then report what it found, briefly:

- **Problems**, grouped by the handoff's items: users, states and journeys; requirements and their source; boundary tests; baselines and targets; the decision log; the sign-off; and, when there's an old slice to replace, the replacement inputs.
- **Decisions waiting on a person:** a missing decision, or a decision with no one named as making it. Never fill these in yourself.
- **Replacing an old slice:** yes or no. It decides whether Planning includes data migration, cut-over and decommissioning.

Don't fix anything unless the person asks. If the project keeps its decision log or Discovery files elsewhere, the person can set `handoff` paths in `.claude/slice-migration.json` (`users`, `decisions`, `architecture`, `data_inventory`, `characterisation`). Suggest these, but don't edit the config to make the check pass.
