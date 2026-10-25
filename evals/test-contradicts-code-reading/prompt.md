---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---

We're replacing a legacy Java EE trading app (IBM DayTrader 8) with a new Python slice. We're in the Discovery phase: drawing requirements from the legacy code and confirming them with characterisation tests against the running legacy app. The legacy code is in `legacy/daytrader8`; Discovery documents are in `docs/discovery/`.

Reading `TradeSLSBBean.sell`, we wrote requirement TRADE-5: "Selling a holding that has already been sold returns a cancelled order; no money moves." The characterisation test for it has just failed: the running app returns HTTP 500 instead, and no money moves.

What exactly should we change in the requirements and the other Discovery documents? Don't edit any files: just tell me.
