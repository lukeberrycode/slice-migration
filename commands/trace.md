---
description: Check the trace from requirements to tests - requirements with no test, and tests tagged with requirements that don't exist
allowed-tools: [Bash, Read]
---

# Trace check

Run:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/trace.py" .
```

Then report what it found, briefly:

- **No test:** for each requirement, say whether a test is due now (the current phase's requirements) or later (for example a new slice's requirement whose test is planned for Execution). Don't write tests unless asked.
- **Unknown requirement:** a test is tagged with an ID that isn't in the requirements file. Usually a typo, or a requirement that was renamed or withdrawn. Say which, if you can tell from the requirements and `keep-or-fix.md`.
- **Checked by hand:** confirm each row says why it can't be automated.

If the project tags tests some other way than `req("ID")`, or keeps tests elsewhere, the person can set `trace.tag` (a regular expression whose first group holds the IDs) and `trace.tests` (folders) in `.claude/slice-migration.json`. Requirements whose tests belong to a later phase can be listed without failing with `trace.exempt` (regular expressions matched against IDs). Suggest these, but don't edit the config to make the check pass.
