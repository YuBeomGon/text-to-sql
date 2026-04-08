# SSOT Guide

SSOT means single source of truth.
This project needs explicit ownership of truth because Claude Code, harness scripts, tests, and prompt assets can drift apart quickly.

## Why this matters

In harness-driven projects, regressions often come from document drift rather than code bugs.
A model follows one file, a script follows another, and a test silently encodes a third rule.
This guide defines where truth lives.

## SSOT hierarchy

When files disagree, use this order.

1. Locked evaluation behavior
2. `program.md`
3. `docs/wbs_v0.1.md`
4. `docs/evaluation_framework.md`
5. `docs/public_db_adaptation.md`
6. `CLAUDE.md`
7. `README.md`
8. implementation notes or comments

## What each file owns

### `program.md`
Owns the operating contract.
It defines how the agent works, what the priorities are, what the hard constraints are, and what counts as done.

### `docs/wbs_v0.1.md`
Owns milestone structure and task decomposition.
It answers what should be built next.

### `docs/evaluation_framework.md`
Owns scoring logic and evaluation definitions.
It answers how success and regression are measured.

### `docs/public_db_adaptation.md`
Owns the public-data reinterpretation of the original task.
It answers why USAspending is used, what slice is in scope, and what error families matter.

### `CLAUDE.md`
Owns Claude Code operating guidance, coding rules, and repo working conventions.
It should not silently redefine product behavior or metric definitions.

### `README.md`
Owns onboarding and navigation.
It should summarize, not redefine deeper rules.

### Config and metadata files
These own concrete values needed at runtime.
Examples:
- dataset slice configuration
- glossary dictionaries
- entity alias tables
- threshold values if they are meant to be tuned

Do not duplicate these values in multiple modules.

## Rules for adding new truth

Before adding a new rule, ask:
- Is this a product behavior rule?
- Is this an evaluation rule?
- Is this a workflow rule?
- Is this a runtime configuration value?

Put it in the one file that owns that category.
Then reference it from other places instead of copying it.

## Anti-patterns

Avoid these failure modes:

### 1. Prompt-only truth
A critical business rule exists only inside one prompt template.
Result: the rule is invisible to tests and easy to forget.

### 2. Test-only truth
A metric definition exists only inside a test assertion.
Result: the team does not know the real policy until a test fails.

### 3. Comment-only truth
A core assumption exists only in comments.
Result: code changes without updating the actual contract.

### 4. Duplicate truth
The same threshold or rule exists in two or three files.
Result: silent drift.

## Preferred storage locations

Use this decision table.

- Agent operating behavior -> `program.md` or `CLAUDE.md`
- Product scope -> `docs/public_db_adaptation.md`
- Scoring and gates -> `docs/evaluation_framework.md`
- Architecture compliance and process quality -> `docs/troubleshooting.md`
- Work decomposition -> `docs/wbs_v0.1.md`
- Improvement attempt history -> `docs/improvement_log.md`
- Collaboration and Git process -> `CONTRIBUTING.md`
- Tunable constants -> config file under a dedicated config directory
- Dataset schema notes -> docs or structured metadata file, not prompt text alone

## Change discipline

If you change any of the following, update SSOT in the same change:
- evaluation thresholds
- ambiguity policy
- accepted public-data scope
- meaning of metrics like obligation or outlay
- required clarification behavior
- WBS milestone boundaries

## Review checklist

Before merging, check:
- Is the new rule stored in the correct owner file?
- Did I reference the rule instead of duplicating it?
- Do tests align with the documented rule?
- Would a new agent know where to find this rule?
