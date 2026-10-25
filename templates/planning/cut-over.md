# Cut-over

## Mechanism

<How the old slice keeps running while the new one takes over, one vertical slice at a time: strangler fig routing, feature flags, or both slices in parallel with their outputs compared. Who or what decides where each request goes.>

## Success criteria, per slice

| Slice | Tests that must pass against the new slice | Live measures (errors, performance) | Agreed by |
|---|---|---|---|

## Rollback

**Triggers:**

| Trigger | Measure | Threshold |
|---|---|---|

**Procedure:**

1. <Step>

**Rehearsal:** <date, who, and what happened. Rehearsed once before the first cut-over.>
