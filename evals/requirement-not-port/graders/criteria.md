---
type: llm
weight: 1
---

A successful answer:

1. States requirements as behaviour at the slice's boundary: what a user or client can observe, or what the slice stores (for example: registering with a new user ID creates an account whose cash and opening balance are the amount given; registering an existing user ID fails and changes nothing). The method counts the data the slice stores as part of its boundary, so requirements and tests about stored records are fine. They are not stated as classes, methods, entity managers, persistence calls or the Java structure.
2. Treats requirements drawn from code as hypotheses to be confirmed by a test against the running legacy app (for example, marks them unconfirmed, or proposes a characterisation test for each). Code reading alone is not presented as settled behaviour.
3. Flags at least one questionable behaviour (for example, that the opening balance isn't validated, or that passwords and card numbers are stored as given) as something for a person to decide, rather than silently "fixing" it in the requirements.

Fail if the requirements mirror the Java (for example "create an AccountProfileDataBean", "call persist on the account"), or if it proposes Python classes that translate the method. Don't fail an answer for describing stored data (such as "one profile and one account, linked by user ID") or for testing through the database.
