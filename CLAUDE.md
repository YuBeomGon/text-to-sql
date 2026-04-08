# CLAUDE.md

This repository is built to be developed with Claude Code using a harness-driven, score-gated workflow.

Read in this order before making changes:
1. `README.md`
2. `docs/project_context.md`
3. the original task PDF uploaded by the user
4. `docs/public_db_adaptation.md`
5. `docs/evaluation_framework.md`
6. `docs/ssot_guide.md`
7. `program.md`
8. `docs/wbs_v0.1.md`
9. `docs/harness_design.md`
10. `CONTRIBUTING.md`

## Project intent

Build a high-precision NL2SQL system for a public database task.
The original internal-looking task is reinterpreted as a public-data problem using USAspending contracts data and DuckDB in-memory.

Success is not "SQL executes".
Success is "semantic meaning is correct, risky answers are minimized, and score does not regress".

## SSOT policy

Follow `docs/ssot_guide.md`.
If two documents disagree, resolve in this order:
1. locked evaluation behavior
2. `program.md`
3. `docs/wbs_v0.1.md`
4. `docs/evaluation_framework.md`
5. `docs/public_db_adaptation.md`
6. `README.md`

Do not create hidden alternative rules in code comments, prompts, or ad hoc scripts.
If behavior changes, update the corresponding SSOT document in the same change.

## Working rules

### Core working model
- Work in very small steps.
- Prefer one WBS item or a narrow subset of one item per change.
- Run `./score.sh --quick` after each meaningful change.
- If score regresses, revert or narrow the scope.
- Update docs when behavior, policy, or scope changes.

### Architecture rules
- Keep DuckDB in-memory as the default execution mode.
- Do not introduce an external DB server.
- Do not replace the public dataset with a custom synthetic schema.
- Do not bypass the interpretation layer and send the raw user question directly to SQL generation.
- Keep semantics, generation, verification, and policy modules separable.

### Safety and answer policy rules
- Prefer clarification or abstention over a risky answer.
- Treat metric meaning, time axis, scope, and entity matching as first-class concerns.
- Never silently guess when the ambiguity is critical.

### Coding rules
- Optimize for readability first.
- Write code that a new teammate can understand quickly.
- Use descriptive names, not clever abbreviations.
- Keep functions focused and reasonably short.
- Minimize nesting and avoid dense control flow.
- Avoid hard-coded business values, magic numbers, prompt fragments, and schema constants when they belong in config, metadata, fixtures, or dictionaries.
- Keep domain definitions centralized.
- Prefer explicit data structures over implicit positional conventions.
- Add comments only when they explain intent, invariants, or non-obvious tradeoffs.
- Do not add comments that merely restate the code.

### Formatting rules
- Use the project's formatter and linter once configured.
- Keep import order stable.
- Keep line length moderate for review readability.
- Prefer one logical concern per file.
- Do not mix unrelated refactors with feature work.

### Testing rules
- Add or update tests when behavior changes.
- Write a failing test before implementation whenever a WBS item can be expressed as a concrete behavior.
- Start each WBS item by defining the expected behavior in a test, fixture, or locked evaluation case.
- Implementation is done only when the new test passes and `./score.sh --quick` does not regress.
- Favor result-set tests, policy tests, and regression tests over brittle string-match tests.
- Lock hard cases once they represent a real failure mode.
- Do not delete a failing hard case to improve score.

### Prompt and rule management
- Do not scatter prompt rules across many files without links.
- Shared prompt policies must live in one referenced location.
- If you add a new prompt contract, document where it is owned.

## Preferred implementation style

Good code in this repository should feel:
- obvious
- modular
- boring in a good way
- easy to extend without guessing hidden rules

Prefer this order of improvement:
1. make semantics explicit
2. make validation explicit
3. make failure modes observable
4. then optimize

## Multi-agent or subagent guidance

For this project, subagents are acceptable and often preferable when token limits are tight.
However:
- keep foundation work single-agent at the start
- only fan out after interfaces, score gates, and ownership boundaries are clear
- assign subagents to narrow ownership areas
- merge one small change at a time through score gates

Recommended default:
- Foundation and architecture: single main agent
- After foundation stabilizes: subagents for `data-eval`, `semantics`, `verifier`, `policy`, and `bench`
- Keep final merge and scoring decisions centralized

## What not to do
- Do not chase exact SQL string match as the primary goal.
- Do not optimize for broad coverage before hard-case reliability.
- Do not make large speculative changes across many modules at once.
- Do not hide important business rules inside prompts only.
- Do not hard-code temporary fixes for one test if they hurt generality.
