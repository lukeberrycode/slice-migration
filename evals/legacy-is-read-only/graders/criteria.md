---
type: llm
weight: 1
---

A successful answer:

1. Advises against patching the legacy app, because it is the test oracle: characterisation tests must record what it actually does, including the HTTP 500.
2. Keeps the test asserting the current behaviour (the server error), and sends the behaviour to a keep-or-fix or decision log so a person can decide that the new slice shows a message instead.
3. Does not give a patch to the legacy Java as the recommended path. (Mentioning that a patch is possible while recommending against it is fine.)

Fail if its main recommendation is to patch the legacy code, or to change the test to expect a message from the legacy app.
