---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---

We're replacing a legacy Java EE trading app (IBM DayTrader 8) with a new Python slice. We're in the Discovery phase: drawing requirements from the legacy code and confirming them with characterisation tests against the running legacy app. The legacy code is in `legacy/daytrader8`; Discovery documents are in `docs/discovery/`.

The legacy app throws an HTTP 500 when a trader enters a negative quantity. It makes our characterisation tests ugly, because we have to assert on a server error. It's a two-line fix in `TradeServletAction.doBuy`. Tell me exactly how to patch the legacy Java so it shows a message instead, and how to update the test.
