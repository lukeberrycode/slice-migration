---
name: planning
description: Run the Planning phase of a legacy slice migration, after the Discovery gate - choose the new slice's stack with an RFC backed by evidence, then plan the data migration, the cut-over and rollback, and the vertical slices in delivery order. Use when Discovery's gate has been approved and the person asks to plan the migration, choose a stack, or plan the cut-over.
---

# Planning

The second phase of `${CLAUDE_PLUGIN_ROOT}/method.md`. It starts only when a person has approved the Discovery gate. It has two gates of its own: the stack, then the plan.

## Rules

- **Plan from the requirements, not the old code.** The signed-off requirements in `docs/discovery/requirements.md` are the input. The old slice's structure is not a design to copy.
- **Evidence over opinion.** Every option in the RFC is judged against named requirements, with evidence: a spike, a measurement, documentation. Where a requirement has a number (throughput, for example), measure each option against the old slice's baseline.
- **Spikes are throwaway.** They live under `docs/planning/rfc-NNNN/spikes/` and never become the new slice's code.
- **Gates belong to people.** You can't write the gates file. At each gate, set out the decisions with your suggestion for each, then stop.
- **Never modify the legacy slice.**

## Part 1: the stack (ends at the stack gate)

0. **Copy the Planning templates** from `${CLAUDE_PLUGIN_ROOT}/templates/planning/` to `docs/planning/`, never overwriting a file that's there. The gate hook allows the RFC, the architecture and the README now, and the rest only after the stack gate.
1. **What the requirements ask of a stack.** In `docs/planning/rfc-0001-destination-stack.md`, list the requirements that constrain the choice: money and precision, performance, security, the interfaces that must not change, how it runs.
2. **Options.** Two to four realistic options, including the people who'll maintain it: what the team knows matters.
3. **Evidence.** For each constraint, a spike or a source. Record how each spike was run, so it can be repeated. Run measurements more than once.
4. **Recommendation**, with the trade-offs stated plainly.
5. **The new slice's architecture**, in `docs/planning/architecture.md`: the same artefacts as Discovery's `architecture.md`, for the new slice.
6. **Stop at the stack gate.** Run `/slice-migration:gate-review stack` and fix what it finds, or list each finding you didn't fix and why. List the decisions for the person. Nothing in Part 2 starts until they approve `stack` in the gates file.

## Part 2: the plan (ends at the plan gate)

7. **Data migration**, `docs/planning/data-migration.md`: schema mapping, scripts, a rollback path, and a check that the new slice reads the old data the same way. If the data stays where it is, say why that's safe.
8. **Cut-over**, `docs/planning/cut-over.md`:
   - the mechanism that avoids a big bang: strangler fig routing, feature flags, or both slices in parallel with outputs compared;
   - success criteria per slice: the characterisation and contract tests passing against the new slice, plus agreed live measures;
   - rollback triggers and the procedure, to be rehearsed once before the first cut-over.
9. **Vertical slices**, `docs/planning/slices.md`: slices that can be delivered and shown whole, in delivery order. Order by risk and dependency (Discovery's risk ranking). For each slice: its requirement IDs, copied from Discovery, and its elements in dependency order. Every requirement must be in exactly one slice; list any that aren't.
10. **Stop at the plan gate.** Run `/slice-migration:gate-review planning` first, as at the stack gate. The person approves the slices, their order and the cut-over plan. Execution can't start until they do.

## Measure the time

Ask the person for their estimate before each part starts, and record the actual time at each gate.
