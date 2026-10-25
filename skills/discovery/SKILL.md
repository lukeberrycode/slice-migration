---
name: discovery
description: Run the Discovery phase of a legacy slice migration - get the old slice running, map its users, states and data, draw requirements from the code as hypotheses, and confirm or correct each with a characterisation test against the running old slice. Use when starting or continuing Discovery on a project set up with /slice-migration:migrate-init, or when asked to find out what a legacy system does before replacing it.
---

# Discovery

The first phase of `${CLAUDE_PLUGIN_ROOT}/method.md`. Read the method's two principles before starting. They are not optional.

## Rules

- **Requirements, not porting.** Describe behaviour at the slice's boundary: its UI, its public API, the calls it makes, the data it stores. Never describe classes or methods, because the new slice won't have them.
- **The old slice is the test oracle.** A requirement drawn from code or documents is a hypothesis until a characterisation test against the running old slice confirms it. When a test shows the reading was wrong, correct the requirement and add a row to `docs/discovery/agent-errors.md`.
- **Odd behaviour goes to `docs/discovery/keep-or-fix.md`**, never straight into the requirements. Describe it, say who depends on it, and suggest keep or fix. The decision belongs to a person.
- **Until a person decides, a requirement says what the legacy slice does**, however odd, with a link to its keep-or-fix entry. Never write the fixed behaviour as a requirement in advance, not even marked "pending". Once the person decides, the new slice's requirement for a fixed quirk gets its own ID, so a reversed behaviour never shares an ID with the legacy one.
- **`agent-errors.md` is for your own misreadings**: where you read the code or documents one way and the running slice did another. When the manual or a config page is wrong, say so in the requirement and its keep-or-fix entry, not in `agent-errors.md`.
- **Never modify the legacy slice.** Changes to how it's built or run go next to it, not in it. The gate hook blocks writes to `legacy_path`.
- **Gates belong to people.** You can't write the gates file, and you mustn't try another way. When Discovery is ready, prepare the gate checklist and stop.

## Steps

Work in this order. Each answer is a file in `docs/discovery/` (the templates are there after `migrate-init`).

1. **Run the old slice locally**, with its data and the services it calls, in containers if you can. Record anything that can't be reproduced in `README.md`.
2. **What does it do?** `one-pager.md`. Use the user manual where there is one: each feature it describes is a high-level requirement.
3. **How does it do it?** `architecture.md`: projects, runtime and build technologies, a diagram, and the boundary the tests will attach to.
4. **What data does it own?** `data-inventory.md`: stores, schemas, volumes, who else reads or writes them, and how money is represented.
5. **Who are its users?** `users-states-journeys.md`. Per user: their states, a risk ranking (money, regulation, data loss), and their journeys.
6. **Requirements.** `requirements.md`, one row per requirement on a state or transition, each with a test method and status *Hypothesis*. Work from the highest-risk states down, and test those most deeply.
7. **Characterisation tests**, in `tests/characterisation/`, against the running old slice. Tag each with its requirement ID. Run them. Update each requirement to *Confirmed* or *Corrected*. A surprising result goes to `keep-or-fix.md` first.
8. **Non-functional requirements** with a number (performance, for example) get a measured baseline on the old slice.
9. **The gate.** Run the trace check (`/slice-migration:trace`): every requirement needs a tagged test or a "By hand" reason. Fill in the checklist in `README.md`, list the decisions that are waiting on a person (scope, keep-or-fix, sign-off), give your suggestion for each, and stop. Planning can't start until a person approves the gate in the gates file.

## Measure the time

The method compares estimated and actual time. Before starting, ask the person for their estimate, or for the estimation method they want to use. At the end, record the actual time: theirs and the agent's.
