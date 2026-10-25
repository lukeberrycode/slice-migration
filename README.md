# slice-migration

A Claude Code plugin for replacing a legacy system slice with a new one. You build the new slice from requirements, not by porting the old code, and people approve every gate.

**Status: work in progress (version 0.1).** The gate hook and the Discovery phase work. The later phases are on the roadmap below.

The method is my own idea (Luke Berry). It's based on my professional experience of project planning and setting quality gates in the era before AI, and on real AI-assisted migrations I have run since then. I developed it with Claude, and turned it into this plugin with Claude Code's help.

[The method](method.md) is an early draft of the process, in plain text. It guided Claude through the Discovery phase of [daytrader-to-python](https://github.com/lukeberrycode/daytrader-to-python), a migration of DayTrader 8 (Java EE) to Python. That phase was estimated at 119.3 hours without AI. With AI following the method, it took 1.26 hours of my time and 1.03 hours of agent time (see its `docs/timings.md`).

## The idea

- **Requirements, not porting.** The old code is read for evidence of behaviour. It is never translated line by line.
- **The old slice is the test oracle.** A requirement the agent draws from code is a hypothesis until a characterisation test against the running old slice confirms it. Where the agent was wrong, that's recorded.
- **People decide at every gate.** The agent prepares the evidence and makes suggestions. A person approves.

## What the plugin enforces

Prose instructions can be ignored, so the important rules are enforced by a `PreToolUse` hook (`hooks/gate.py`):

| Rule | How |
|---|---|
| No work on a phase until every earlier gate is approved | Writes to a phase's paths are blocked until earlier phases have `approved_by` and `date` in the gates file |
| Only a person approves a gate | The agent can't write the gates file, with file tools or from the shell |
| The legacy slice is read-only | Writes under `legacy_path` are blocked |
| A broken config doesn't switch the gates off | An unreadable config or gates file blocks; it doesn't allow |

The hook has 13 tests (`tests/test_gate.py`), which run in CI. `scripts/demo.sh` runs a real Claude Code session that is told to skip ahead and approve its own gates, and checks that it can't.

**Known limits in 0.1.** The shell check looks for the gates file's path in the command, so a deliberately disguised command could get past it. Writes to gated paths from the shell (rather than with the file tools) aren't checked yet. For a hard guarantee, also add a `deny` rule for the gates file in the project's `.claude/settings.json` and use Claude Code's sandbox.

## Use

```
/plugin marketplace add lukeberrycode/slice-migration
/plugin install slice-migration@slice-migration
```

Or, from a local clone: `claude --plugin-dir path/to/slice-migration`.

Then, in the project that holds the legacy slice:

1. `/slice-migration:migrate-init legacy/my-app` writes `.claude/slice-migration.json` and copies the Discovery templates to `docs/discovery/`.
2. Ask Claude to start Discovery. The `discovery` skill takes it through the phase, step by step.
3. `/slice-migration:migrate-status` shows the gates, the current phase and what's waiting on a person.
4. When you've reviewed Discovery, approve its gate yourself in `docs/gates.json`:

```json
{ "discovery": { "approved_by": "Your name", "date": "2026-10-25" } }
```

### Config

`.claude/slice-migration.json` (default in `templates/config.json`):

```json
{
  "legacy_path": "legacy",
  "gates_file": "docs/gates.json",
  "phases": [
    { "name": "discovery", "paths": ["docs/discovery/*", "tests/characterisation/*"] },
    { "name": "planning", "paths": ["docs/planning/*"] },
    { "name": "execution", "paths": ["src/*", "tests/*"] },
    { "name": "decommission", "paths": ["docs/decommission/*"] }
  ]
}
```

A path belongs to the first phase that matches it, so `tests/characterisation/` is Discovery's, and other tests are Execution's. `*` matches across folders.

## Roadmap

1. Skills for the later phases: planning (the destination RFC, data migration, cut-over and rollback, vertical slices), execution per slice, decommissioning and evaluation.
2. Agents: a requirements extractor, an oracle tester, a trace auditor (every requirement to its tests and code), and a gate reviewer.
3. A trace check run as a hook: no requirement without a test.
4. Per-language settings (for example Python's `decimal.Decimal` rule for money) as optional skills.
5. `claude plugin eval` cases, drawn from the mistakes recorded in daytrader-to-python's `agent-errors.md`.
6. A replay of DayTrader's Discovery with the plugin, compared with the original. Then a second, unfamiliar legacy app.

## Timings

See `docs/timings.md`.

## Licence

Apache 2.0.
