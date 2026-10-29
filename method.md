This document is a recipe to build a new system slice (comprising one or more products) from requirements: either to replace a legacy slice, or from a new design.

It is based on my professional experience performing similar operations.

The method has two halves. **Discovery** produces signed-off requirements, each with a way to test it. **Delivery** (planning, execution and evaluation) builds the new slice from those requirements. Delivery doesn't care how Discovery was done, only that its output meets [the Discovery handoff](#the-discovery-handoff). So Discovery has two sources, which can be used alone or together:

- **From the old slice.** The requirements are drawn out of a legacy slice and confirmed against it. The new slice should replace the old and fulfil the same role as the old one did, in such a way that surrounding products are as oblivious to the change as possible. Internally, the new slice works better: it is more maintainable, more testable and more future-proof, and having clear requirements records, maintained going forward by AI, will make it easier to refactor in the future. It's designed to work both with an old slice I am familiar with AND one that I am new to.
- **From a new design.** There is no old slice, or it isn't the authority on what the product should do. The requirements come from the design of the new product, and are confirmed by the people it's for.

A redesign of a legacy slice uses both: requirements for what's kept come from the old slice, and requirements for what changes come from the new design.

When there's an old slice to replace, Delivery also moves its data, cuts over from it without a big bang, and decommissions it. These steps are marked **[REPLACEMENT]** in the timeline, and are skipped when nothing is being replaced.

Below is a rough generic timeline for these projects.
The format is a nested series of **questions**, with the type of **answer** that each needs following in _italics_.
Every **answer** is a **document or artifact of some kind** that either fulfils the project or feeds future steps.

AI is used at every point:
- to help refine every question
- to help deliver the documents/artifacts that comprise the answers
- where appropriate, to form a piece of the final product

People decide at every **[GATE]**: nothing after a gate starts until the named answer has been reviewed and approved by a person.

Where **requirements** are mentioned, these can be functional or non-functional (performance, security, regulatory, observability and so on), but all are rooted in the end user experience.

Time is **measured** throughout: estimate each phase before it starts, and record the actual time when it ends. The comparison is the evidence for what AI made faster.

## A guiding principle

The plan specifically avoids rewriting code line by line, method by method, class by class or even module by module. Requirements are defined, and the new slice is built from the ground up to meet them. Where there is an old slice, useful lessons learned in its creation should be transmitted forward to the new slice by defining them as functional or non-functional requirements.

## A second principle: every requirement is tested at the slice's boundary

A requirement is only a hypothesis until something confirms it, and every requirement gets a test written at the slice's boundary (its UI, its public API, the calls it makes to other services, the data it stores). Tests at the boundary describe behaviour rather than code, so the same tests run against the new slice, and passing them is part of accepting it. This doesn't break the guiding principle: the tests define behaviour, not structure.

What confirms a requirement depends on where it came from:

- **From the old slice, the old slice is the test oracle.** Requirements that AI draws out of code and documents are only a hypothesis about what the old slice does. Tests run against the running old slice confirm or correct that hypothesis.
- **From a new design, people are the oracle.** There's nothing yet to run the tests against. A requirement is confirmed by the people it's for: through a prototype, user research or a walkthrough of their journeys. Its boundary test is still written in Discovery, and fails until Execution builds what it tests.

## Generic timeline

- Discovery (from the old slice, from a new design, or both; every source ends at the same gate)
  - From the old slice:
    - Can we run the old slice locally, with its data and the services it calls? _a working local environment (containerised if possible) and a note of anything that can't be reproduced_
    - What does the product do? _a general high-level one-pager_
    - How does it do it? _a list of existing projects, their runtime technologies, their build/test/tooling technologies, and an architecture diagram_
    - What data does the slice own, and in what form? _a data inventory: stores, schemas, volumes, and who else reads or writes the data_
    - Who are its **users**? _a list of users (the priority is the consumers, but also consider producers, sponsors. Client software products that interface with the slice via public API, and services whose public API the slice interacts with, also count as users)_
      - Per user, what are the **states** of the product as experienced by each user? _a list of states_
      - Which states carry the most risk (money, regulation, data loss)? _a risk ranking of the states. Every state is still covered; the ranking sets the order of work and the depth of discovery and testing_
        - Per state, what are the **requirements** of that state? _a list of requirements_
          - Per requirement, how do we **test** that requirement? _a test method_
            - Per test, do we need any mocking tools? _list of mocking tools_
      - Per user, what are the **journeys** taken by users through these states? _a high-level state map_
        - Per state transition, what are the **requirements** of that transition? _a list of requirements_
          - Per requirement, how do we **test** that requirement? _a test method_
            - Per test, do we need any mocking tools? _list of mocking tools_
    - Does the old slice actually behave as the requirements say? _characterisation (golden-master) tests at the slice's boundary, run against the old slice and passing, with each test traced to its requirement. Contract tests for client software and upstream services (e.g. Pact). If the old slice has no tests, this is where they're written. Unit tests on the old code are optional: they can't carry over, but they can be given to the AI as extra evidence, and are worth writing only where logic can't be observed from the boundary. A test that records surprising behaviour goes to the keep-or-fix log, not straight into the requirements_
    - Where the old slice's behaviour is odd, wrong or undocumented, do we keep it or fix it? _a decision log: each quirk, who depends on it, and the decision with its reason. Kept quirks become requirements; fixed ones become requirements for the corrected behaviour_
  - From a new design:
    - What problem does the product solve, and for whom? _a one-pager: the problem, the outcome it should bring, and what's out of scope_
    - What does it have to work within? _the services it calls and the client software that will call it, with their APIs; the data it will own and where that data comes from; regulatory, security and performance limits, each with a target where it has a number_
    - Who are its **users**, and per user, what **states** and **journeys** should the product have? Which states carry the most risk? What are the **requirements** of each state and transition, how do we **test** each one, and do the tests need any mocking tools? _the same answers as for the old slice (users, states, a risk ranking, journeys, requirements, test methods and mocking tools), designed rather than observed_
    - Do the people it's for agree that this is what they need? _each requirement confirmed with them through a prototype, user research or a walkthrough of the journeys, with the confirmation recorded against the requirement_
    - What have we assumed? _a decision log: each assumption or open question, the risk if it's wrong, and the decision with who made it and its reason_
    - Can each requirement be tested at the slice's boundary? _a boundary test per requirement, traced to it, written now and failing until Execution builds what it tests. Contract tests for the services it calls and for its client software_
  - From both (a redesign of an old slice): _the old slice's steps for what's kept, the design's steps for what changes, with each requirement's source recorded_
  - **[GATE]** Are the requirements, the test methods and the decisions approved? _signed-off requirements, meeting the Discovery handoff. This is also where anything AI identified as a requirement can be dropped, with the reason recorded_
- Planning:
  - What technologies to use in the new slice? _an RFC (or ADR) setting out the options considered and the evidence for each, measured against the non-functional requirements' baselines or targets, then the new slice's projects, runtime technologies, build/test/tooling technologies and architecture diagram_
  - **[GATE]** Is the destination stack approved? _the RFC's decision_
  - **[REPLACEMENT]** How does the data move? _a data migration plan: schema mapping, migration scripts, a rollback path, and a check that the new slice reads the old data the same way (or a reason it doesn't need to, if the data stays where it is)_
  - Plan going live:
    - **[REPLACEMENT]** How can we maintain the old slice, and control cut-over to the new slice, to prevent a 'big bang' change? _cut-over mechanism and plan: strangler fig routing, feature flags, or running both slices in parallel and comparing their outputs_
    - How do we know a slice has gone live successfully? _success criteria per slice: the boundary and contract tests from Discovery passing against the new slice, plus agreed live measures (errors, performance)_
    - What makes us roll back, and how? _rollback triggers and the rollback procedure (to the old slice, where there is one), rehearsed once before the first slice goes live_
  - What are the vertical slices of the product, that can be delivered and presented whole? _a list of vertical slices, in delivery order_
    - Per vertical slice:
      - What are the requirements of that slice? _a requirements list - taken directly from the discovery phase_
      - What is the dependency order of the elements of that slice? _a list of elements in dependency order_
  - **[GATE]** Are the slices, their order and the go-live plan (with the cut-over, when replacing) approved?
- Execution:
  - Per slice:
    - Per element:
      - Create the element and run tests. _the element, every one of its requirements traced to passing tests and to the code that meets it, 100% tests passed_
    - **[GATE]** Is the slice accepted? _the slice's boundary and contract tests from Discovery passing against the new slice; human review of the code_
    - Put the slice live (**[REPLACEMENT]** cutting over from the old slice). _the slice live, with its success criteria met (or rolled back, with the reason recorded)_
    - Continuous evaluation:
      - What lessons can be learned? _list of lessons learned_
        - Per lesson:
          - What changes need to be made to existing documents? _list of changes_
            - Per change:
              - Make the changes. _new version of existing documents_
  - **[REPLACEMENT]** Decommission the old slice:
    - What can be switched off and deleted once every slice has cut over? _a decommissioning list (code, infrastructure, data, pipelines, documentation), then the old slice removed. Record what was retired, e.g. lines of code and services_
- Evaluation
  - How long did it take against the estimates? _a table of estimated and actual times per phase_
  - Future-Proofing:
    - Add mechanisms (AI powered if necessary) to:
      - Automate code reviews
      - Ensure that changes to code have corresponding changes to docs - including requirements docs. (Requirements docs and agent control settings are the default programming interface after a project such as this).
      - Keep the trace from each requirement to its tests and its code up to date, so it can be audited at any time.

## The Discovery handoff

Delivery starts from what the Discovery gate approves, and from nothing else. Whatever the source, Discovery hands over:

1. **Users, states and journeys**, with the risk ranking of the states. Delivery orders its vertical slices by it.
2. **The requirements.** Each one has an ID; the state or transition it belongs to; the requirement itself, as behaviour at the slice's boundary; its test method; and its **source**: _old slice_ (legacy behaviour, kept), _fixed_ (a legacy quirk, corrected by a keep-or-fix decision) or _design_ (new). Dropped requirements are listed, with the reason and who decided.
3. **A boundary test for every requirement**, traced to its ID, or the reason it's checked by hand. From the old slice, the tests pass against the old slice. From a new design, they fail until Execution builds what they test. Either way, the trace from requirement to test is checked the same way.
4. **A number for every non-functional requirement that has one:** a baseline measured on the old slice, or a target set by the design.
5. **The decision log**, so that every requirement can be traced to why it's there: keep-or-fix decisions from the old slice, and assumptions and open questions from a new design. Each decision names the person who made it.
6. **The sign-off:** the Discovery gate, approved by a person.

When there's an old slice to replace, Discovery also hands over the **replacement inputs**: a working local environment for the old slice, its architecture, its data inventory, and its characterisation and contract tests. Their presence is what switches on Delivery's **[REPLACEMENT]** steps. Delivery never needs to know which source produced a requirement, only whether there's something to replace.

How the requirements were reached (reading the old code, running characterisation tests, design workshops, prototypes) stays with Discovery, along with its working records, such as where AI misread the old slice. Delivery doesn't read them.

## Prioritising

Success means every signed-off requirement is met (when replacing, a 100% swap of new for old), so nothing is left out. Prioritising means three things, each at its own step:

1. **Order:** what goes into which vertical slice, and in what order ("What are the vertical slices…?").
2. **Dropping:** at the requirements gate, whether anything AI identified as a requirement can be dropped, with the reason recorded (this ties in with the keep-or-fix and assumption decisions).
3. **Depth:** the most discovery and testing effort on the highest-risk states, less on low-risk ones ("Which states carry the most risk?").

## Changes

The method is refined as it's used. Each change gets a dated line here; the git history has the detail.

- **23 October 2026:** first public version, from Luke's draft, with: the old slice as test oracle; human gates; non-functional requirements; measured times; a working local environment; a data inventory; a risk ranking of states; characterisation and contract tests; a keep-or-fix log; an RFC for the destination stack; data migration, cut-over, success criteria and rollback; traceability; decommissioning; estimated against actual times. Decided: tests for an old slice without them are written in the "Does the old slice actually behave…?" step; "prioritise" means order, dropping and depth.
- **29 October 2026:** Discovery and Delivery split by a handoff, so the requirements can come from an old slice, a new design or both. Added: Discovery from a new design; the Discovery handoff; a source for each requirement; targets as well as baselines; **[REPLACEMENT]** steps, skipped when nothing is being replaced. The second principle now covers both sources: the old slice is the oracle for requirements drawn from it, and people are the oracle for a new design. "Planning the Migration" and "Executing the Migration" are now "Planning" and "Execution". The Generic Timeline is formatted as a list. The plugin doesn't follow this yet: it runs Discovery from the old slice only.
