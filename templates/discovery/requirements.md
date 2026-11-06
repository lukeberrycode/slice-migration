# <Legacy slice>: requirements

Requirements start as a hypothesis drawn from the code. A characterisation test against the running old slice confirms or corrects each one. Tests carry the requirement's ID (for example `@pytest.mark.req("<ID>")`).

**IDs and links** follow "IDs and links" in the method. A requirement's ID is its state's or transition's ID, then `_REQ` and an optional index. Each ID starts with its anchor, and each row links back to its state or transition. For example, a row's first cells are `<a id="CONS_BROWSING_REQ_1"></a>CONS_BROWSING_REQ_1` and `[CONS_BROWSING](users-states-journeys.md#CONS_BROWSING)`.

**Status:** *Hypothesis* = from the code, not yet tested; *Confirmed* = a passing characterisation test; *Corrected* = the test showed the code-reading was wrong, and the requirement now says what the slice does (also logged in `agent-errors.md`); *By hand* = checked against the running slice by hand, with the reason.

Behaviour that looks wrong is described as it is, with a link to `keep-or-fix.md`. The gate decides whether the new slice keeps it.

**Source** (the Discovery handoff in `method.md`): *old slice* = the legacy behaviour, kept; *fixed* = a legacy quirk, corrected by a keep-or-fix decision, whose entry the row links to (for example `[KF-3](keep-or-fix.md#KF-3)`); *design* = new.

## Scope (decided at the gate)

| # | Question | Suggestion | Decision | Decided by |
|---|---|---|---|---|

## Features in the manual, and their requirements

| Feature | Requirements |
|---|---|

## Requirements

| ID | State or transition | Requirement | Test | Source | Status |
|---|---|---|---|---|---|

## Non-functional requirements

Each one belongs to the state or transition where the user feels it. One that spans several has a row on each.

| ID | State or transition | Requirement | Measure | Baseline or target | Source | Status |
|---|---|---|---|---|---|---|

## Dropped (decided at the gate)

| ID | State or transition | Requirement | Reason | Decided by |
|---|---|---|---|---|
