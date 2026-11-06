# Discovery

The first phase of the method (`method.md` in the slice-migration plugin), run on <slice>.

Every document here is Markdown, and every item in it can be linked to: a table row starts with an anchor (`<a id="..."></a>`) named after its ID or its name, and anything else has a heading.

This file covers both Discovery sources. Keep the questions and the checklist for this project's source, and delete the others.

## Questions: from the old slice

| Question | Answer |
|---|---|
| Can we run the old slice locally? | <how to run it; anything that can't be reproduced> |
| What does it do? | `one-pager.md` |
| How does it do it? | `architecture.md` |
| What data does it own? | `data-inventory.md` |
| Who are its users; their states, risks and journeys? | `users-states-journeys.md` |
| What are the requirements, and how is each tested? | `requirements.md`, `tests/characterisation/` |
| Does the old slice behave as the requirements say? | <number of characterisation tests, passing against the old slice> |
| Keep or fix the odd behaviour? | `keep-or-fix.md` |
| What did the agent get wrong? | `agent-errors.md` |

## Questions: from a new design

| Question | Answer |
|---|---|
| What problem does it solve, and for whom? | `one-pager.md` |
| What does it have to work within? | `constraints.md` |
| Who are its users; their states, risks and journeys? | `users-states-journeys.md` |
| What are the requirements, and how will each be tested? | `requirements.md` |
| Do the people it's for agree that this is what they need? | `requirements.md`, under *Confirmed by* |
| What have we assumed? | `assumptions.md` |

## Gate: status

**Not yet approved.** A person approves the gate by adding `"discovery": {"approved_by": "<name>", "date": "<YYYY-MM-DD>"}` to `docs/gates.json`. The agent can't write that file.

### Checklist: from the old slice

- [ ] Every functional requirement confirmed or corrected by a characterisation test, or the reason it can't be recorded.
- [ ] Every feature in the user manual traced to at least one tested requirement.
- [ ] A measured baseline for each non-functional requirement that has a number.
- [ ] Scope decisions made, with reasons (person).
- [ ] Every keep-or-fix entry decided (person).
- [ ] Requirements signed off, including anything dropped and the reason (person).

### Checklist: from a new design

- [ ] Every requirement has a test method concrete enough to write its boundary test from: the set-up, what's done at the boundary, and what's checked.
- [ ] A target for each non-functional requirement that has a number, recorded in `constraints.md` with who set it and why.
- [ ] Every requirement confirmed by the people it's for, and recorded under *Confirmed by* (person).
- [ ] Scope decisions made, with reasons (person).
- [ ] Every assumption and open question decided (person).
- [ ] Requirements signed off, including anything dropped and the reason (person).
