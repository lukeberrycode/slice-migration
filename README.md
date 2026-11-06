# slice-migration

A Claude Code plugin for replacing a legacy system slice with a new one. You build the new slice from requirements, not by porting the old code, and people approve every gate.

**Status: work in progress (version 0.2).** The gate hook and the Discovery and Planning phases work. The later phases are on the roadmap below.

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
| Shell commands follow the same rules | Redirections, `tee`, `cp`, `mv`, `touch`, `sed -i`, `dd of=`, `git checkout --` and the like are checked against the gates, following `cd` |
| The legacy slice is read-only | Writes under `legacy_path` are blocked |
| A broken config doesn't switch the gates off | An unreadable config or gates file blocks; it doesn't allow |
| A second pair of eyes before each gate | The `gate-reviewer` agent can only read (Read, Glob, Grep; a test keeps it that way). It reports findings with evidence and never recommends passing |

The hook's tests (`tests/test_gate.py`) run in CI. `scripts/demo.sh` runs a real Claude Code session that is told to skip ahead and approve its own gates, and checks that it can't.

**Known limits.** The shell check reads commands the way they're usually written. It's a guard against mistakes, not a sandbox: a script, `python -c` or a disguised command can write without the parser seeing it. For a hard guarantee, also add a `deny` rule for the gates file in the project's `.claude/settings.json`, and run Claude Code's sandbox with write access only to the paths of the current phase.

## Use

```
/plugin marketplace add lukeberrycode/slice-migration
/plugin install slice-migration@slice-migration
```

Or, from a local clone: `claude --plugin-dir path/to/slice-migration`.

Then, in the project that holds the legacy slice:

1. `/slice-migration:migrate-init legacy/my-app` writes `.claude/slice-migration.json` and copies the Discovery templates to `docs/discovery/`.
2. Ask Claude to start Discovery. The `discovery` skill takes it through the phase, step by step. After the Discovery gate, the `planning` skill does the same for Planning, which has two gates: the stack, then the plan.
3. `/slice-migration:migrate-status` shows the gates, the current phase and what's waiting on a person.
4. `/slice-migration:trace` lists requirements with no test, and tests tagged with requirements that don't exist.
   `/slice-migration:handoff` checks that Discovery's output meets the method's Discovery handoff, which is all Planning starts from.
5. `/slice-migration:gate-review` has the read-only `gate-reviewer` agent check the phase before you decide its gate, and saves its report in `docs/reviews/`.
6. When you've reviewed Discovery, approve its gate yourself in `docs/gates.json`:

```json
{ "discovery": { "approved_by": "Your name", "date": "2026-10-25" } }
```

### Config

`.claude/slice-migration.json` (default in `templates/config.json`; for a new design, `templates/config-design.json`, which has no `legacy_path`, reads its decisions from `assumptions.md`, and gives Discovery `tests/contract/*` rather than `tests/characterisation/*`):

```json
{
  "legacy_path": "legacy",
  "gates_file": "docs/gates.json",
  "phases": [
    { "name": "discovery", "paths": ["docs/discovery/*", "tests/characterisation/*"] },
    { "name": "stack", "paths": ["docs/planning/README.md", "docs/planning/rfc-*", "docs/planning/architecture.md"] },
    { "name": "planning", "paths": ["docs/planning/*"] },
    { "name": "execution", "paths": ["src/*", "tests/*"] },
    { "name": "decommission", "paths": ["docs/decommission/*"] }
  ]
}
```

A path belongs to the first phase that matches it, so `tests/characterisation/` is Discovery's, and other tests are Execution's. Likewise the stack RFC and the new architecture belong to the `stack` phase, and the rest of `docs/planning/` waits for the stack gate. `*` matches across folders.

## Trace check

`scripts/trace.py` checks that every requirement has a test and that every test tag names a real requirement. A requirement is a table row in the requirements file whose first cell is an ID, such as `CONS_BROWSING_REQ_1` (see [IDs and links](method.md#ids-and-links)). Older IDs such as `AUTH-1` are still recognised here, so existing projects keep this check. A test is traced to it by a tag such as `@pytest.mark.req("CONS_BROWSING_REQ_1")`; the same text works in any language. Rows that say "By hand" count as traced, and are listed separately. It exits 1 if anything is untraced, so it can run in CI:

```
python3 path/to/slice-migration/scripts/trace.py .
```

On `daytrader-to-python` after its Discovery gate, it reports 61 requirements, 37 traced to tests and 1 checked by hand (ADMIN-4), which matches that repository's own record. The 23 without tests are the new slice's requirements, whose tests are planned for Execution, and the three non-functional requirements, which are checked by a measured baseline or by the set-up rather than by tagged tests.

Optional `trace` settings in `.claude/slice-migration.json`, with their defaults:

```json
"trace": {
  "requirements": "docs/discovery/requirements.md",
  "tests": ["tests"],
  "tag": "req\\(([^)]*)\\)",
  "exempt": []
}
```

`tag` is a regular expression whose first group holds the IDs. `exempt` lists ID patterns to report but not fail, such as `"^CONS_CHECKOUT_"` for requirements whose tests come in a later phase.

## Handoff check

`scripts/handoff.py` checks that Discovery's output meets [the Discovery handoff](method.md#the-discovery-handoff): what Planning and later phases start from, whether the requirements came from an old slice, a new design or both. It checks:

1. Users, states, transitions and journeys in `users-states-journeys.md`, with a risk for every state. (The Mermaid state diagrams are for people, and aren't checked.)
2. Every requirement links back to a state or transition, and has a test method and a source (*Old slice*, *Fixed* or *Design*), and none is still a *Hypothesis*. A *Fixed* requirement names its keep-or-fix entry. A dropped one has a reason and who decided.
3. Every *Old slice* requirement has a tagged boundary test or a "By hand" reason, using the trace check's settings: the old slice is there to confirm it now. A *Fixed* or *Design* requirement needs only its test method, because nothing can pass its test yet. It's listed as "Tests due in Execution", where its test is written before what it tests. `trace.exempt` doesn't apply here: whether a test is due now depends on the requirement's source, not its ID.
4. Every non-functional requirement with a measure has a baseline or a target.
5. Every row of the decision log (`keep-or-fix.md`, and the scope decisions in `requirements.md`) has a decision and who made it.
6. A person has approved the Discovery gate. `--before-sign-off` skips this, for use before the gate.

It also checks [IDs and links](method.md#ids-and-links). Every user, state, transition and requirement needs a well-formed, unique ID and an anchor, and must link back to the definitions its ID says it depends on. Every link to an anchor or a heading in the users, requirements and decision log files must lead somewhere. A heading is reached by its generated anchor (`## Quote latency` by `#quote-latency`), but a definition needs its own anchor even if it also has a heading. Older IDs such as `AUTH-1` don't pass, so an existing project has to move to the new IDs before this check can pass.

When `legacy_path` exists, it's replacing an old slice, so it also checks the replacement inputs: the old slice's architecture, its data inventory, and the characterisation tests. It exits 1 if anything is missing:

```
python3 path/to/slice-migration/scripts/handoff.py --before-sign-off .
```

It checks structure, not meaning: that a decision names someone, not that they're a person. The `gate-reviewer` checks the meaning. Optional `handoff` paths in `.claude/slice-migration.json`, with their defaults:

```json
"handoff": {
  "users": "docs/discovery/users-states-journeys.md",
  "decisions": ["docs/discovery/keep-or-fix.md"],
  "architecture": "docs/discovery/architecture.md",
  "data_inventory": "docs/discovery/data-inventory.md",
  "characterisation": "tests/characterisation"
}
```

A Discovery from a new design would list its assumptions log in `decisions`.

## Roadmap

1. Discovery from a new design, the method's second Discovery source: a skill, templates, `migrate-init` and status support, gate-reviewer items and evals. The plan is in [docs/plans/discovery-from-a-new-design.md](docs/plans/discovery-from-a-new-design.md).
2. Skills for the later phases: execution per slice, decommissioning and evaluation.
3. Agents: a requirements extractor and an oracle tester, alongside the gate reviewer.
4. The trace check extended from requirements and tests to code, and run at each gate.
5. Per-language settings (for example Python's `decimal.Decimal` rule for money) as optional skills.
6. More eval cases: one per phase rule, and cases that run in a scaffolded project rather than an empty folder.
7. A replay of DayTrader's Discovery with the plugin, compared with the original. Then a second, unfamiliar legacy app.

## Evals

`evals/` holds five cases for `claude plugin eval`. Each one tests a rule of the method that a real run broke or nearly broke in daytrader-to-python: a test contradicting the code-reading, writing requirements rather than porting, a person owning the gate, the legacy slice staying read-only, and odd behaviour going to keep-or-fix. Each case runs with the plugin and without it, and an LLM judge grades the answer against written criteria.

```
claude plugin eval . --runs 3 --judge-model sonnet
```

Results on 25 October 2026 (3 runs per arm, Sonnet judge, $3.65 in total):

| Case | With plugin | Without | Difference |
|---|---|---|---|
| A person owns the gate | 1.00 | 0.33 | +0.67 |
| The legacy slice is read-only | 1.00 | 1.00 | 0 |
| Odd behaviour goes to keep-or-fix | 1.00 | 0.00 | +1.00 |
| Requirements, not porting | 1.00 | 0.67 | +0.33 |
| A test contradicts the code-reading | 0.67 | 0.00 | +0.67 |
| **Mean** | **0.93** | **0.40** | **+0.53** |

Three runs per arm is a small sample, so treat single cases with care. The first run of the suite found two faults, both fixed before these results: the Discovery skill didn't say that a requirement keeps the legacy behaviour until a person decides, and one grader was stricter than the method (it failed requirements about stored data, which the method counts as part of the boundary). The default judge (Haiku) gave inconsistent verdicts on the same answer, so the results above use Sonnet.

## Timings

See `docs/timings.md`.

## Maintenance tasks

- **Pinned runner upkeep.** CI runs on a pinned image (`runs-on: ubuntu-24.04` in `.github/workflows/test.yml`), so it won't update itself. Change the label by hand before GitHub retires that image ([supported runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners#supported-runners-and-hardware-resources)). The tests use the image's own `python3`, so a new image can also mean a new Python version: check that the Test workflow passes after the change.

## Licence

Apache 2.0.
