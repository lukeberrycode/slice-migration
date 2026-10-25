# Planning

The second phase of the method (`method.md` in the slice-migration plugin), run on <legacy slice>.

| Question | Answer |
|---|---|
| What technologies will the new slice use? | `rfc-0001-destination-stack.md`, `architecture.md` |
| How does the data move? | `data-migration.md` |
| How do we cut over without a big bang, know it worked, and roll back? | `cut-over.md` |
| What are the vertical slices, and in what order? | `slices.md` |

## Stack gate: status

**Not yet approved.** A person approves it by adding `"stack": {"approved_by": "<name>", "date": "<YYYY-MM-DD>"}` to `docs/gates.json`.

- [ ] Every constraint in the RFC traced to a requirement.
- [ ] Evidence for each option against each constraint, with how to repeat it.
- [ ] The new slice's architecture drawn.
- [ ] The decision, and the reason (person).

## Plan gate: status

**Not yet approved.** A person approves it by adding `"planning": {"approved_by": "<name>", "date": "<YYYY-MM-DD>"}` to `docs/gates.json`.

- [ ] Data migration plan, with a rollback path and a read-back check.
- [ ] Cut-over mechanism, success criteria per slice, rollback triggers and procedure.
- [ ] Every requirement in exactly one vertical slice.
- [ ] The slices, their order and the cut-over plan approved (person).
