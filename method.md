This document is a recipe to migrate a legacy system slice (comprising one or more products) to a new slice. 

It is based on my professional experience performing similar operations. 

The new slice should replace the old and fulfil the same role as the old one did, in such a way that surrounding products are as oblivious to the change as possible. Internally, the new slice works better: it is more maintainable, more testable and more future-proof, and having clear requirements records, maintained going forward by AI, will make it easier to refactor in the future.

It's designed to work both with an old slice I am familiar with AND one that I am new to.

Below is a rough generic timeline for these tech migration projects.
The format is a nested series of **questions**, with the type of **answer** that each needs following in _italics_.
Every **answer** is a **document or artifact of some kind** that either fulfils the migration or feeds future steps.

AI is used at every point:
- to help refine every question
- to help deliver the documents/artifacts that comprise the answers
- where appropriate, to form a piece of the final product

People decide at every **[GATE]**: nothing after a gate starts until the named answer has been reviewed and approved by a person.

Where **requirements** are mentioned, these can be functional or non-functional (performance, security, regulatory, observability and so on), but all are rooted in the end user experience.

Time is **measured** throughout: estimate each phase before it starts, and record the actual time when it ends. The comparison is the evidence for what AI made faster.

## A guiding principle

The plan specifically avoids rewriting code line by line, method by method, class by class or even module by module. Requirements are defined, and the new slice is built from the ground up to meet them. Useful lessons learned in the creation of the old slice should be transmitted forward to the new slice by defining them as functional or non-functional requirements.

## A second principle: the old slice is the test oracle

Requirements that AI draws out of code and documents are only a hypothesis about what the old slice does. Tests run against the running old slice confirm or correct that hypothesis. Tests written at the slice's boundary (its UI, its public API, the calls it makes to other services, the data it stores) describe behaviour rather than code, so the same tests can then run against the new slice, and passing them is part of the cut-over acceptance. This doesn't break the guiding principle: the tests define behaviour, not structure.

## Generic timeline

- Discovery
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
  - **[GATE]** Are the requirements, the test methods and the keep-or-fix decisions approved? _signed-off requirements list. This is also where anything AI identified as a requirement can be dropped, with the reason recorded_
- Planning the Migration:
  - What technologies to use in the new slice? _an RFC (or ADR) setting out the options considered and the evidence for each, then the same artifacts as in the answer to the 'How does it do it?' question in the discovery phase, except referring to the new slice_
  - **[GATE]** Is the destination stack approved? _the RFC's decision_
  - How does the data move? _a data migration plan: schema mapping, migration scripts, a rollback path, and a check that the new slice reads the old data the same way (or a reason it doesn't need to, if the data stays where it is)_
  - Plan the cut-over:
    - How can we maintain the old slice, and control cut-over to the new slice, to prevent a 'big bang' change? _cut-over mechanism and plan: strangler fig routing, feature flags, or running both slices in parallel and comparing their outputs_
    - How do we know a cut-over has succeeded? _success criteria per slice: the characterisation and contract tests passing against the new slice, plus agreed live measures (errors, performance)_
    - What makes us roll back, and how? _rollback triggers and the rollback procedure, rehearsed once before the first cut-over_
  - What are the vertical slices of the product, that can be delivered and presented whole? _a list of vertical slices, in delivery order_
    - Per vertical slice:
      - What are the requirements of that slice? _a requirements list - taken directly from the discovery phase_
      - What is the dependency order of the elements of that slice? _a list of elements in dependency order_
  - **[GATE]** Are the slices, their order and the cut-over plan approved?
- Executing the Migration:
  - Per slice:
    - Per element:
      - Create the element and run tests. _the element, every one of its requirements traced to passing tests and to the code that meets it, 100% tests passed_
    - **[GATE]** Is the slice accepted? _the slice's characterisation and contract tests passing against the new slice; human review of the code_
    - Cut over to the new slice. _the slice live, with its success criteria met (or rolled back, with the reason recorded)_
    - Continuous evaluation:
      - What lessons can be learned? _list of lessons learned_
        - Per lesson:
          - What changes need to be made to existing documents? _list of changes_
            - Per change:
              - Make the changes. _new version of existing documents_
  - Decommission the old slice:
    - What can be switched off and deleted once every slice has cut over? _a decommissioning list (code, infrastructure, data, pipelines, documentation), then the old slice removed. Record what was retired, e.g. lines of code and services_
- Evaluation
  - How long did it take against the estimates? _a table of estimated and actual times per phase_
  - Future-Proofing:
    - Add mechanisms (AI powered if necessary) to:
      - Automate code reviews
      - Ensure that changes to code have corresponding changes to docs - including requirements docs. (Requirements docs and agent control settings are the default programming interface after such a tech migration as this).
      - Keep the trace from each requirement to its tests and its code up to date, so it can be audited at any time.

## Prioritising

Success means a 100% swap of new for old, so nothing is left out. Prioritising means three things, each at its own step:

1. **Order:** what goes into which vertical slice, and in what order ("What are the vertical slices…?").
2. **Dropping:** at the requirements gate, whether anything AI identified as a requirement can be dropped, with the reason recorded (this ties in with the keep-or-fix decisions).
3. **Depth:** the most discovery and testing effort on the highest-risk states, less on low-risk ones ("Which states carry the most risk?").

## Changes

The method is refined as it's used. Each change gets a dated line here; the git history has the detail.

- **23 October 2026:** first public version, from Luke's draft, with: the old slice as test oracle; human gates; non-functional requirements; measured times; a working local environment; a data inventory; a risk ranking of states; characterisation and contract tests; a keep-or-fix log; an RFC for the destination stack; data migration, cut-over, success criteria and rollback; traceability; decommissioning; estimated against actual times. Decided: tests for an old slice without them are written in the "Does the old slice actually behave…?" step; "prioritise" means order, dropping and depth.
