# Program Specification

## Objective

Build a high-precision NL2SQL system on top of public spending data.

Initial locked data slice (core):
- USAspending public data
- contracts only
- fiscal years 2024-2025
- 5 core awarding agencies: DoD, HHS, NASA, DHS, GSA
- DuckDB in-memory only

Extended evaluation agencies (robustness, after foundation stabilizes):
- Department of Veterans Affairs, Department of Energy, Department of Transportation

Project target:
- positive result accuracy >= 0.99 on the locked hard set
- execution success >= 0.995
- negative abstain precision >= 0.98
- risky answer rate <= 0.02
- no external DB server

## Working Model

You are not optimizing for SQL style.
You are optimizing for semantic correctness.

Always prioritize:
1. correct metric meaning
2. correct time interpretation
3. correct scope and state filters
4. correct entity resolution
5. safe abstain or clarification over risky answers

## How You Work

1. Read `README.md`
2. Read `docs/project_context.md`
3. Read the original task PDF uploaded by the user
4. Read `docs/public_db_adaptation.md`
5. Read `docs/evaluation_framework.md`
6. Read `docs/ssot_guide.md`
7. Read `docs/wbs_v0.1.md`
8. Find the next unchecked item in milestone order
9. Implement only that item or a very small subset of it
10. Run `./score.sh --quick`
11. If score improved or stayed equal, keep the change
12. If score regressed, revert and try a narrower approach
13. Mark the completed WBS item as `[x]`
14. Repeat

## Hard Constraints

- Do not replace the public-data scope with a custom private schema.
- Do not introduce an external database server.
- Keep DuckDB in-memory as the default execution mode.
- Do not weaken tests to improve score.
- Do not optimize for exact SQL string match.
- Prefer result-set correctness.
- Prefer abstain / clarify over risky answers.
- Keep code modular so retrieval, generation, validation, and policy can evolve separately.

## Key Product Principle

Never send the raw user question directly to SQL generation without interpretation.

Before SQL generation, the system should try to derive a structured intermediate meaning that includes:
- metric
- entity
- time range
- scope
- sort / ranking
- ambiguity flags

## Development Priorities

### Phase 1 priorities
- schema retrieval
- glossary / metric dictionary
- time interpreter
- entity resolver
- SQL static validator
- retry / repair loop

### Phase 2 priorities
- multi-candidate generation
- semantic reranking
- uncertainty scoring
- abstain / clarify policy
- hard-case regression lock

## Definition of Done

A feature is not done when SQL executes.
A feature is done when:
- the relevant score does not regress
- new tests are added if needed
- failure mode is categorized
- docs are updated if behavior changes

## Non-Goals

At the current stage, do not optimize for:
- broad multi-domain coverage
- multi-tenant deployment
- full UI polish
- distributed execution
- all USAspending award types

## Expected Behavior on Ambiguous Questions

If a question is ambiguous on a critical axis, do one of the following:
- ask a clarification question
- abstain with a short explanation

Critical ambiguity axes:
- amount meaning
- fiscal year vs calendar year
- award date vs action date
- awarding agency vs funding agency
- prime awards vs all awards

## Merge Gate Reminder

The project should move like this:
- small change
- quick score
- keep or revert
- update WBS
- continue

No large speculative branch is preferred over many small validated steps.


## Repo governance

- Follow `CLAUDE.md` for coding style, subagent guidance, and working rules.
- Follow `docs/ssot_guide.md` for source-of-truth ownership.
- Follow `CONTRIBUTING.md` for branch, commit, and PR strategy.
