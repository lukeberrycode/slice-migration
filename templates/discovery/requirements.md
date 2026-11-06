# <Slice>: requirements

Requirements start as a hypothesis. What confirms one depends on where it came from:

- **From the old slice:** it's drawn from the code. A characterisation test against the running old slice confirms or corrects it.
- **From a new design:** it's drawn from the design. The people it's for confirm it, through a prototype, user research or a walkthrough of their journeys. Its boundary test is written first in Execution, so for now *Test* holds a test method concrete enough to write it from: the set-up, what's done at the boundary, and what's checked.

Tests carry the requirement's ID (for example `@pytest.mark.req("<ID>")`).

**IDs and links** follow "IDs and links" in the method. A requirement's ID is its state's or transition's ID, then `_REQ` and an optional index. Each ID starts with its anchor, and each row links back to its state or transition. For example, a row's first cells are `<a id="CONS_BROWSING_REQ_1"></a>CONS_BROWSING_REQ_1` and `[CONS_BROWSING](users-states-journeys.md#CONS_BROWSING)`.

**Status:** *Hypothesis* = not yet tested or confirmed; *Confirmed* = from the old slice, a passing characterisation test; from a new design, a person's confirmation, recorded under *Confirmed by*. Only for the old slice: *Corrected* = the test showed the code-reading was wrong, and the requirement now says what the slice does (also logged in `agent-errors.md`); *By hand* = checked against the running slice by hand, with the reason.

**Confirmed by** (only for a new design): who confirmed it, how and when, for example "Trader walkthrough, Sam, 12 Nov". Only a person can confirm a requirement, and the agent never fills this in on its own judgement. Leave it empty for a requirement from the old slice.

From the old slice, behaviour that looks wrong is described as it is, with a link to `keep-or-fix.md`. The gate decides whether the new slice keeps it.

**Source** (the Discovery handoff in `method.md`): *old slice* = the legacy behaviour, kept; *fixed* = a legacy quirk, corrected by a keep-or-fix decision, whose entry the row links to (for example `[KF-3](keep-or-fix.md#KF-3)`); *design* = new. A design requirement links to any assumption it rests on (for example `[AS-2](assumptions.md#AS-2)`), and a non-functional one to its constraint (for example `[Quote latency](constraints.md#quote-latency)`).

## Scope (decided at the gate)

| # | Question | Suggestion | Decision | Decided by |
|---|---|---|---|---|

## Features in the manual, and their requirements

Only for the old slice. Delete this section for a new design.

| Feature | Requirements |
|---|---|

## Requirements

| ID | State or transition | Requirement | Test | Source | Status | Confirmed by |
|---|---|---|---|---|---|---|

## Non-functional requirements

Each one belongs to the state or transition where the user feels it. One that spans several has a row on each.

| ID | State or transition | Requirement | Measure | Baseline or target | Source | Status | Confirmed by |
|---|---|---|---|---|---|---|---|

## Dropped (decided at the gate)

| ID | State or transition | Requirement | Reason | Decided by |
|---|---|---|---|---|
