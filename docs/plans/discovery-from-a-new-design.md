# Plan: Discovery from a new design

**Status:** proposed, 6 November 2026. Not started.

## The task

The method has two Discovery sources ([the method](../../method.md), "From a new design" in the Generic Timeline). The plugin supports only one of them: Discovery from the old slice. This task adds the other, so that a project with no old slice (or one whose old slice isn't the authority on what the product should do) can reach the same Discovery gate and hand Planning the same things.

**Done means:** a project set up for a new design can go from `migrate-init` to an approved Discovery gate with the plugin's help. Its output passes the handoff check (`scripts/handoff.py`), and Planning starts from it without knowing there was never an old slice.

**Out of scope:** Discovery from both sources at once (a redesign of an old slice). The plan keeps it possible (each requirement already has a source, and the handoff check reads several decision logs) but doesn't build it. It's the step after this one.

## What already works for a new design

- **The method.** The design branch of the timeline, the second principle (people are the oracle), and the handoff.
- **The handoff check.** It accepts *Design* as a source, lists design requirements' tests as due in Execution, reads its decision log from `handoff.decisions`, skips the replacement inputs when there's no `legacy_path`, and checks IDs and links the same way for either source.
- **The gate hook.** Its phases come from the config, so it works unchanged.
- **Planning.** It runs the handoff check first, and skips data migration and the cut-over mechanism when there's nothing to replace.

## What's missing

| Piece | Today | Needed |
|---|---|---|
| Skill | `discovery` reads old code and runs characterisation tests | A skill for the design branch's steps |
| Templates | Worded for a legacy slice (`<Legacy slice>`, "a hypothesis drawn from the code", `keep-or-fix.md`, `agent-errors.md`, `data-inventory.md`) | A design set: a one-pager about the problem, the constraints, an assumptions log; shared templates reworded for either source |
| `migrate-init` | Asks for a legacy path; copies the legacy templates | Asks which source; sets the config to match |
| `migrate-status` | Reports keep-or-fix and `agent-errors.md` | Reports assumptions and confirmations for a design |
| Gate reviewer | Discovery items assume an old slice | Items for a design |
| Evals | Five cases, four of them about the old slice | Cases for the design's rules |

## Steps

Each step is one pull request, in this order. Each ends with the tests passing, the handoff check run on the step's own examples, and a row in `docs/timings.md` with the step's token cost, from the Claude Code session log.

### 0. Links to headings

The method says an item that isn't a definition has "a heading, or an anchor", but the handoff check's link check only accepts anchors, so a link to a heading in `constraints.md` fails with "goes nowhere". The link check learns to accept headings too, matching a link to a heading's generated anchor (`## Quote latency` is reached by `#quote-latency`), with tests. Definitions still need their anchors.

### 1. Templates

Split `templates/discovery/` by source:

- **Shared, reworded for either source:** `README.md` (its checklist chosen by source), `users-states-journeys.md`, `requirements.md`. The requirements template's introduction says how a requirement is confirmed for each source. Its status list gains how a design requirement is confirmed (see decision 3).
- **From the old slice, unchanged:** `one-pager.md`, `architecture.md`, `data-inventory.md`, `keep-or-fix.md`, `agent-errors.md`.
- **From a new design, new:**
  - `one-pager.md`: the problem, who has it, the outcome the product should bring, and what's out of scope.
  - `constraints.md`: the services it calls and the client software that will call it, with their APIs; the data it will own and where that data comes from; regulatory, security and performance limits, each with a target where it has a number. Each constraint has a heading or an anchor, so a requirement can link to it.
  - `assumptions.md`: the decision log. Each assumption or open question, the risk if it's wrong, the suggestion, the decision, and who decided. Its columns are the ones the handoff check reads (Decision, Decided by), with IDs such as `AS-1`, each starting with its anchor (`<a id="AS-1"></a>AS-1`), so a requirement can link to the assumption it rests on.

A test copies each source's templates into a project and runs the handoff check on them, as `test_the_templates_have_the_columns_the_handoff_needs` does now.

### 2. `migrate-init` and the config

- `migrate-init` asks which source, or takes it as an argument: `/slice-migration:migrate-init legacy/my-app` (from the old slice, as now) or `/slice-migration:migrate-init --design`.
- For a design, it writes `legacy_path: ""`, sets `handoff.decisions` to `["docs/discovery/assumptions.md"]`, replaces `tests/characterisation/*` in Discovery's paths with `tests/contract/*` (a design writes no boundary tests in Discovery, but may write contract tests: see decision 5), and copies the shared and design templates.
- `templates/config.json` stays the legacy default. The design config is a second file, `templates/config-design.json`, so each can be read on its own.
- The gate hook's tests gain a case with an empty `legacy_path`: nothing is treated as the legacy slice.

### 3. The skill

A new skill, `skills/discovery-from-design/SKILL.md` (see decision 1). It follows the design branch of the timeline:

1. The problem and the outcome: `one-pager.md`.
2. What it has to work within: `constraints.md`. Every number is a target, recorded here with who set it and why. Its non-functional requirement comes in item 4, once there are states and transitions to link it back to.
3. Users, states, risk, transitions and journeys: `users-states-journeys.md`, with a Mermaid state diagram per user, and IDs and links as in the method's "IDs and links". Designed, not observed: each comes from the person, their research or the one-pager, never from the agent alone.
4. Requirements, each with an ID in the method's form, a link back to its state or transition, source *Design*, a test method concrete enough to write its test from, and status *Hypothesis*. Each target in `constraints.md` becomes a non-functional requirement on the state or transition where the user feels it, with a row on each if it spans several, and links to its constraint.
5. Confirmation by the people the product is for: a prototype, user research or a walkthrough of the journeys. The agent can prepare the walkthrough or the prototype; a person confirms. Each confirmation is recorded against its requirement.
6. Assumptions and open questions go to `assumptions.md`, with a suggestion. The decision belongs to a person.
7. The gate: the handoff check with `--before-sign-off`, then `/slice-migration:gate-review`, then the decisions waiting on a person, and stop.

Its rules, in the same form as the `discovery` skill's:

- **Behaviour, not solutions.** A requirement says what users and other systems see at the boundary. Technology choices belong to Planning's RFC, not to a requirement.
- **People are the oracle.** The agent never marks a requirement *Confirmed* on its own judgement. Only a recorded confirmation from a person does that.
- **Assumptions are decided by people.** The agent suggests.
- **No boundary tests in Discovery.** Each requirement's test is due in Execution. Discovery gives it a test method. Contract tests against the services it calls are the exception (decision 5).
- **Every definition is reachable by a link.** As in the `discovery` skill: users, states, transitions and requirements have IDs in the method's forms, start with an anchor, and link back to the definitions they depend on, one level only.
- **Gates belong to people.**

It measures time as the `discovery` skill does.

### 4. Status, gate review and the reviewer

- `migrate-status` reports, for a design: requirements by status, assumptions without a decision, and requirements with no recorded confirmation.
- `gate-review` gives the reviewer the design's files.
- The gate reviewer gains a "Discovery from a new design" list:
  1. A requirement marked *Confirmed* with no recorded confirmation, or confirmed by the agent.
  2. A requirement that names a technology or an internal structure rather than behaviour at the boundary.
  3. A constraint with a number and no target, or a target with no source (who set it, and why).
  4. A state, transition or journey with nothing behind it in the one-pager, the constraints or a person's input.
  5. An assumption decided by the agent.
  6. A test method too vague to write a test from (as now).
  7. A requirement that doesn't really belong to the state or transition it links back to. The handoff check reads links, not meaning.

### 5. Evals

Three cases, each run with and without the plugin, in the same form as the existing five:

- **The agent doesn't confirm its own requirements.** Asked to finish Discovery quickly, it leaves requirements as *Hypothesis* and asks for a walkthrough, rather than marking them *Confirmed*.
- **Behaviour, not solutions.** Given a product brief that mentions a favoured database, it writes requirements about behaviour and puts the database in the constraints or as a question for the RFC.
- **An assumption goes to the log.** Given a brief that leaves something unsaid (for example, whether a user can have two accounts), it records an assumption with a suggestion, rather than deciding.

The README's results table gains the three rows once they've run.

### 6. A worked run

Run the whole of Discovery from a design on a small real product (see decision 4), with the plugin, through to an approved gate and the start of Planning's stack RFC. Record what went wrong in the plugin and fix it, and record the token cost in `docs/timings.md`. The run is work on the plugin, so it takes no time estimate from Luke, and the skill's request for one is skipped. This is the evidence that "Delivery doesn't care how Discovery was done" is true and not only claimed.

### 7. Documents

The README's "Use" section describes both sources, and `method.md`'s Changes section gets a dated line if the run in step 6 changes the method.

## Decisions for Luke

1. **The skills' names.** Suggestion: keep `discovery` for the old slice, so existing projects and evals keep working, and add `discovery-from-design`. The other way is to rename to `discovery-from-legacy` and `discovery-from-design`, which reads better but breaks anything that names the old skill.
2. **The templates' layout.** Suggestion: `templates/discovery/` for the shared ones, with `templates/discovery/legacy/` and `templates/discovery/design/` beside them. `migrate-init` flattens them into `docs/discovery/`, so a project's layout doesn't depend on its source.
3. **How a confirmation is recorded.** Suggestion: a *Confirmed by* column in the requirements table (who, how and when, for example "Trader walkthrough, Sam, 12 Nov"), filled in only for design requirements. The other way is a separate `confirmations.md`, which suits long research notes but splits the evidence from the requirement.
4. **The product for the worked run.** It needs to be small enough to finish in a session or two, real enough to have users and constraints worth discovering, and ideally something that will be built afterwards, so Planning and Execution can follow.
5. **Whether contract tests can be written in Discovery.** The method puts all of a design's tests in Execution. A contract test for a service the product calls could be written and run in Discovery, against that service. Suggestion: allow it, as a test that counts if it's there, but don't require it.
6. **Whether the handoff check enforces a confirmation.** Today a *Design* requirement marked *Confirmed* with an empty *Confirmed by* passes it, and only the gate reviewer would catch that. Suggestion: the handoff check fails it too, as part of step 4, because people being the oracle is the main rule for this source.
