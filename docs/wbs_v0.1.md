# WBS v0.1

## Milestone M0 - Foundation

- [ ] Create repository skeleton for `src/`, `tests/`, `eval/`, `datasets/`, `harness/`, `docs/`
- [ ] Add DuckDB in-memory bootstrap module
- [ ] Add config for data slice selection: fiscal years, agencies, award type
- [ ] Add dataset loader for public USAspending contract slice
- [ ] Add raw schema inspection utility
- [ ] Add base query executor
- [ ] Add evaluation harness skeleton
- [ ] Add quick/full score CLI contract

## Milestone M1 - Dataset and Evaluation

- [ ] Normalize the 300 hard cases into a machine-readable format
- [ ] Tag each case with polarity, failure axis, expected behavior, difficulty
- [ ] Add result-set comparison logic
- [ ] Add negative/ambiguous expected behavior schema
- [ ] Add paraphrase expansion framework
- [ ] Add temporal fuzz expansion framework
- [ ] Add score report output format
- [ ] Lock an initial hard regression set

## Milestone M2 - Semantic Interpretation Layer

- [ ] Add schema retrieval module
- [ ] Add glossary retrieval module
- [ ] Add metric dictionary module
- [ ] Add time interpreter module
- [ ] Add scope interpreter module
- [ ] Add entity normalization module
- [ ] Add intermediate representation for parsed question meaning
- [ ] Add ambiguity flagging at the interpretation stage

## Milestone M3 - Baseline Generation Layer

- [ ] Add prompt pack v1 for public contracts domain
- [ ] Add question-to-IR conversion path
- [ ] Add IR-to-SQL generation path
- [ ] Add answer rendering path
- [ ] Add basic execution trace logging
- [ ] Add smoke tests for end-to-end generation

## Milestone M4 - Validation and Repair

- [ ] Add static schema validator
- [ ] Add invalid column / invalid table detection
- [ ] Add join sanity checks
- [ ] Add metric-definition checks
- [ ] Add time-axis checks
- [ ] Add scope/state checks
- [ ] Add retry / repair loop
- [ ] Add repair success metrics

## Milestone M5 - High Precision Policy Layer

- [ ] Add ambiguity router for answer vs clarify vs abstain
- [ ] Add multi-candidate SQL generation
- [ ] Add candidate ranking
- [ ] Add uncertainty scoring
- [ ] Add risky-answer suppression policy
- [ ] Add hard-case memory / cache for repeated failure patterns
- [ ] Add paraphrase robustness checks

## Milestone M6 - Productization and Benchmarking

- [ ] Add CLI entrypoint
- [ ] Add API or Slack-facing adapter skeleton
- [ ] Add structured logs and traces
- [ ] Add regression CI command
- [ ] Add benchmark report template
- [ ] Add demo script for common scenarios
- [ ] Add release checklist

## Ordering Rules

1. Finish M0 before broad parallelization.
2. M1 and M2 can partially overlap after M0 is stable.
3. M4 should not begin seriously until M3 baseline works.
4. M5 should begin only after M4 metrics are visible.
5. M6 is not a substitute for correctness work.

## Review Rules

Every completed item should satisfy all of the following:

- Code exists and runs
- Relevant tests exist or were updated
- `./score.sh --quick` passes without regression
- The item is small enough to explain in a short commit message

## Notes for Claude Code

When uncertain, prefer splitting a large unchecked item into smaller internal subtasks rather than editing many modules at once.
