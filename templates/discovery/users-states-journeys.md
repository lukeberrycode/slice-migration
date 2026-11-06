# <Legacy slice>: users, states and journeys

IDs and links follow "IDs and links" in the method. Each row's ID starts with its anchor, so that it can be linked to, and each definition links back to what it depends on. A reviewer can follow those links from any requirement back to its user. For example, a state's first cells are `<a id="CONS_BROWSING"></a>CONS_BROWSING`, `Browsing` and, under User, `[CONS](#CONS)`.

## Users

Consumers first, then producers and sponsors. Client software that calls the slice's public API, and services whose API the slice calls, are users too. A user's ID is 3 to 6 capital letters based on their name, such as `CONS` for consumers.

| ID | User | How they use it | Priority |
|---|---|---|---|

## States, per user

Risk is about money, regulation and data loss. Every state is covered; the risk sets the order of work and the depth of testing. A state's ID is `USER_STATE`. A name of several words uses hyphens, such as `CONS_READY-TO-SHIP`.

| ID | State | User | Entered by | Risk |
|---|---|---|---|---|

## Transitions, per user

A transition's ID is `USER_STATE1_TO_STATE2`, and it links back to both states.

| ID | Transition | From | To |
|---|---|---|---|

## Journeys, per user

A Mermaid diagram (`stateDiagram-v2`) of each user's states and transitions, then their journeys.

| Journey | User | Transitions, in order |
|---|---|---|
