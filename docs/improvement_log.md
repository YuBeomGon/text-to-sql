# Improvement Log

This file records every improvement attempt by the agent. Each entry documents what was tried, what score changed, and whether it was kept or reverted.

Read this file before starting a new improvement to avoid repeating failed approaches.

## Format

```
### YYYY-MM-DD — [kept/reverted] short description
- **Target**: which category or gate
- **Change**: what was modified
- **Before**: score before the change
- **After**: score after the change
- **Why kept/reverted**: reasoning
- **Commit**: hash (if kept)
```

## Log

### 2026-04-08 — kept: add agency alias mapping to prompt
- **Target**: easy_baseline (EASY-004, EASY-008, EASY-017)
- **Change**: added agency abbreviation→full name mapping and rule to system prompt
- **Before**: 17/20 (85%) — LLM used "DHS", "HHS" instead of full names
- **After**: 19/20 (95%)
- **Why kept**: fixed 2 of 3 failures, no regressions
- **Commit**: ec4a95f

### 2026-04-08 — kept: add transaction vs award count rule
- **Target**: easy_baseline (EASY-017)
- **Change**: added rule distinguishing "transactions"=COUNT(*) vs "awards"=COUNT(DISTINCT award_id)
- **Before**: 19/20 (95%) — LLM used COUNT(DISTINCT) for transaction count question
- **After**: 20/20 (100%)
- **Why kept**: fixed last easy_baseline failure, no regressions
- **Commit**: 830d64f

### 2026-04-08 — reverted: prompt patching approach
- **Target**: all easy_baseline
- **Change**: rolled back hardcoded agency aliases and count rules from prompt_builder.py
- **Before**: 20/20 (100%) via prompt patching
- **After**: baseline reset — approach violated AC-3 (no hardcoded rules in prompt)
- **Why reverted**: prompt patching is a shortcut that doesn't scale. Architecture compliance gate (AC-1~AC-5) now enforces IR-based pipeline.
- **Commit**: 1c0a8e5
- **Lesson**: result score alone is insufficient — process quality (AC gate) must also pass

### 2026-04-08 — kept: IR-based pipeline rebuild
- **Target**: architecture compliance + all easy_baseline
- **Change**: rebuilt pipeline with IR (entity_resolver → metric_interpreter → time_interpreter → scope_interpreter → ambiguity_detector → prompt_builder from IR)
- **Before**: 0/20 (no pipeline) or 20/20 (prompt patching, reverted)
- **After**: 16/20 (80%) — structurally correct approach
- **Why kept**: AC-1~AC-5 all PASS. Failures are config gaps, not architecture problems.
- **Commit**: multiple (9fd9d42 through fd6429d)

### 2026-04-08 — kept: add aggregation keywords to metric dictionary
- **Target**: easy_baseline (EASY-009, EASY-012, EASY-020)
- **Change**: added aggregation_keywords section to metric_dictionary.yaml (average→AVG, largest→MAX, minimum→MIN), updated metric_interpreter to use detected aggregation type
- **Before**: 16/20 (80%) — "average", "minimum", "largest" not recognized
- **After**: 19/20 (95%)
- **Why kept**: config-based fix, AC-3 compliant. Remaining failure (EASY-011) is DoD data not downloaded.
- **Commit**: f76c703

### 2026-04-09 — baseline: 50-case smoke test
- **Target**: all categories
- **Change**: expanded smoke test from 20 to 50 cases (20 easy + 20 hard answer + 10 clarify)
- **Score**: 36/50 (72%)
  - easy_baseline: 19/20 (95%)
  - entity_resolution: 3/4 (75%)
  - join_aggregation: 1/4 (25%)
  - metric_ambiguity: 11/14 (79%)
  - missingness_linked: 2/4 (50%)
  - scope_state: 0/4 (0%)
- **Next**: attack scope_state (0%) first, then join_aggregation (25%)

### 2026-04-09 — kept: glossary notes + subagency detection + ILIKE hint
- **Target**: scope_state (0%), join_aggregation (25%)
- **Change**: added sql_note fields to glossary.yaml (prime=all rows, no status column, subagency column), prompt_builder loads glossary notes, scope_interpreter detects subagency, added ILIKE hint to prompt rules
- **Before**: 36/50 (72%)
- **After**: 38/50 (76%)
- **Regressions**: missingness_linked 2/4 → 1/4 (-1)
- **Improvements**: easy_baseline +1, join_aggregation +2
- **Unresolved**: scope_state still 0/4, missingness regression
- **Why kept**: net +2, but need to investigate missingness regression
- **Commit**: ba170ea
