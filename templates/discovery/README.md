# Discovery

The first phase of the method (`method.md` in the slice-migration plugin), run on <legacy slice>.

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

## Gate: status

**Not yet approved.** A person approves the gate by adding `"discovery": {"approved_by": "<name>", "date": "<YYYY-MM-DD>"}` to `docs/gates.json`. The agent can't write that file.

- [ ] Every functional requirement confirmed or corrected by a characterisation test, or the reason it can't be recorded.
- [ ] Every feature in the user manual traced to at least one tested requirement.
- [ ] A measured baseline for each non-functional requirement that has a number.
- [ ] Scope decisions made, with reasons (person).
- [ ] Every keep-or-fix entry decided (person).
- [ ] Requirements signed off, including anything dropped and the reason (person).
