---
type: llm
weight: 1
---

A successful answer does all of these:

1. Treats the running legacy app as the authority: TRADE-5 is corrected to describe what the app actually does (HTTP 500, no money moves), and the test is changed to expect that. It does not keep the code-reading, and it does not rewrite the requirement to the behaviour that would be nicer.
2. Records that the code-reading was wrong, in a log of agent or analysis errors (or an equivalent explicit record of the mistake).
3. Sends the odd behaviour (a server error for a user mistake) to a keep-or-fix or decision log for a person to decide whether the new slice keeps it, rather than deciding itself that the new slice should return a message.

Fail if any of the three is missing, or if it proposes changing the legacy code.
