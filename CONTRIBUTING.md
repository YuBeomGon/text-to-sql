# CONTRIBUTING.md

This repository is intended to be developed with small, score-gated changes.
The goal is not maximum coding speed. The goal is steady progress without semantic regressions.

## Branch strategy

Use short-lived branches.
Recommended naming:
- `feat/<area>-<short-topic>`
- `fix/<area>-<short-topic>`
- `chore/<area>-<short-topic>`
- `docs/<topic>`

Examples:
- `feat/semantics-time-interpreter`
- `fix/verifier-award-vs-transaction-count`
- `docs/refresh-eval-guide`

Avoid long-running branches that change many modules at once.

## Commit strategy

Prefer small commits that each do one thing.
A commit should ideally contain one of these shapes:
- one focused behavior change
- one refactor with no behavior change
- one doc update linked to a behavior change
- one test lock for a known failure mode

Recommended commit style:
- `feat(semantics): add fiscal-year interpreter`
- `fix(verifier): reject ambiguous amount meaning`
- `test(eval): lock recipient alias regression`
- `docs(ssot): clarify owner of scoring thresholds`

## Pull request strategy

Keep PRs narrow.
A good PR should answer:
- what failure mode changed
- what module changed
- what score moved, if any
- what tests were added or updated
- what SSOT document changed, if any

### PR template

#### Summary
- What changed?
- Why now?

#### Scope
- Modules touched
- WBS item addressed

#### Evaluation
- `./score.sh --quick` result before
- `./score.sh --quick` result after
- `./score.sh --full` if relevant

#### Risks
- What could regress?
- What ambiguity remains?

#### Docs
- Which SSOT or workflow docs were updated?

## Review rules

Review for:
- semantic clarity
- modularity
- absence of hidden hard-coding
- test quality
- SSOT alignment
- manageable diff size

Do not approve a PR that:
- weakens tests to raise score
- hides business logic in prompts only
- changes multiple architectural areas without a strong reason
- introduces undocumented thresholds or constants

## Coding style expectations

- Prefer readable code over clever code.
- Prefer explicit domain names over abbreviations.
- Prefer config-driven values over literals.
- Prefer composition over giant multi-purpose classes or scripts.
- Keep files easy to scan.
- Keep functions narrow in responsibility.

## Formatting and tooling

Once formatter and linter are configured, run them before merge.
Do not include unrelated formatting churn in a behavior PR.

## Definition of a healthy contribution

A healthy contribution:
- improves or protects score
- explains the failure mode it addresses
- preserves readability
- keeps the rule in the correct source of truth
