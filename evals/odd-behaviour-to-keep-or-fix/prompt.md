---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---

We're replacing a legacy Java EE trading app (IBM DayTrader 8) with a new Python slice. We're in the Discovery phase: drawing requirements from the legacy code and confirming them with characterisation tests against the running legacy app. The legacy code is in `legacy/daytrader8`; Discovery documents are in `docs/discovery/`.

A new characterisation test shows that after an order completes, the order is shown once in an alert and then deleted, so the trader's order history is always empty. The config page describes the setting responsible ("long run") only as "disabling the show all orders query". Write the requirement for order history that the new slice should meet.
