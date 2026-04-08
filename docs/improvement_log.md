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
