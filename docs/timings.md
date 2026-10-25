# Timings

Each piece of work is estimated before it starts, and the actual time is recorded when it ends. The same approach as `daytrader-to-python` (its `docs/timings.md` and `docs/estimation.md`).

## Version 0.1: the minimal working subset

**Scope:** the gate hook, the Discovery skill, `migrate-init` and `migrate-status`, Discovery templates, tests for the hook, and a README with the roadmap.

**Estimate (with AI), made 25 October 2026 at 11:38, before work started.** Claude's per-step judgement, from the pace measured in `daytrader-to-python`. Not formula-based, so treat it with care.

| Step | Agent | Luke |
|---|---|---|
| Config: only what the gate hook and Discovery skill need | 15 min | 15 min |
| Discovery templates and gate checklist | 10 min | 10 min |
| `plugin.json`, Discovery skill, `migrate-init`, `migrate-status` | 25 min | 15 min |
| Gate hook and legacy read-only rule | 30–45 min | 15 min |
| Tests showing the hook blocks, then allows after approval | 15 min | 5 min |
| README with roadmap; repository made public | 10 min | 10 min |
| **Total** | **1.75 h** | **1.25 h** |

Hard deadline: about 15:38. If the hook isn't proven working by about 14:10, version 0.1 is not claimed.

No estimate without AI has been made yet. That's Luke's to make.

| | Started | Finished | Luke (h) | Agent (h) | Tokens / cost |
|---|---|---|---|---|---|
| Version 0.1 | 25 Oct 2026 11:38 | 25 Oct 2026 11:52 (merged) | 0.17 (10 minutes: review, the end-to-end demo, merge) | 0.17 (11:38 to the pull request at about 11:48) | Subscription. 23.6k output, 1.84M cache-read, 37.5k cache-write; API-equivalent $1.14 |

Against the estimate of 1.75 hours of agent time and 1.25 hours of Luke's. Two attempts by the agent to run the end-to-end demo itself were refused by Claude Code's permission checks, so Luke ran `scripts/demo.sh` (PASS). Token figures are from the Claude Code session log (`usage` on each response, 11:38 to 11:49), priced as in `daytrader-to-python`'s `docs/timings.md`: Opus 5.5, per million tokens, input $4.00, output $20.00, cache read $0.20, cache write $8.00.

## Version 0.2

**Estimate (with AI), made 25 October 2026 at 11:58, before work started.** Claude's per-step judgement, rescaled by 0.1's actual pace (about 10 times faster than its estimate). One pull request each.

| Step | Agent | Luke |
|---|---|---|
| Gate hook: check shell commands that write to gated paths, with tests | 10 min | 5 min |
| Trace check: requirements without tests, and tests tagged with unknown requirements; run against `daytrader-to-python` as a real case | 10 min | 5 min |
| Planning skill and templates: RFC, data migration, cut-over and rollback, vertical slices | 10 min | 10 min |
| **Total** | **0.5 h** | **0.33 h** |

| | Started | Finished | Luke (h) | Agent (h) | Tokens / cost |
|---|---|---|---|---|---|
| Shell writes | 25 Oct 2026 11:58 | | | | |
| Trace check | | | | | |
| Planning skill | | | | | |
