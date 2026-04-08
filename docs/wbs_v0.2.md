# WBS v0.2

Changes from v0.1:
- M0 complete, M1 partial — carried forward
- M2 refocused on IR-based pipeline (not prompt patching)
- M3 (Baseline Generation) absorbed into M2 — pipeline already exists, needs IR integration
- M5 multi-candidate generation removed (cost decision)
- Architecture Compliance gate added as cross-cutting concern
- Agency scope reduced to 3 downloaded (HHS, NASA, DHS)

## Milestone M0 - Foundation — COMPLETE

- [x] Create repository skeleton
- [x] Add DuckDB in-memory bootstrap module
- [x] Add config for data slice selection
- [x] Add dataset loader for public USAspending contract slice
- [x] Add raw schema inspection utility
- [x] Add base query executor
- [x] Add evaluation harness skeleton
- [x] Add quick/full score CLI contract
- [x] Add data download automation
- [x] Add data bootstrap script

## Milestone M1 - Dataset and Evaluation — PARTIAL

- [x] Normalize hard cases into machine-readable format
- [x] Tag each case with polarity, failure axis, expected behavior, difficulty
- [x] Add result-set comparison logic
- [x] Add negative/ambiguous expected behavior schema
- [x] Add score report output format
- [x] Add gold SQL for 20 easy baseline cases
- [ ] Add paraphrase expansion runner
- [ ] Add temporal fuzz expansion runner
- [ ] Lock an initial hard regression set

## Milestone AC - Architecture Compliance Gate

- [ ] Implement `src/eval/architecture_check.py` (AC-1 through AC-5)
- [ ] Wire AC gate into `score.sh`
- [ ] Verify current codebase fails AC-3 (hardcoded prompt rules removed but IR not yet in place)

## Milestone M2 - IR-Based Pipeline

### Config and metadata
- [ ] Create `config/agency_aliases.yaml` — agency abbreviation → full name mapping
- [ ] Create `config/metric_dictionary.yaml` — metric term → column name mapping
- [ ] Create `config/glossary.yaml` — domain term definitions

### IR modules
- [ ] Add IR dataclass (`src/ir.py`) — structured representation of parsed question meaning
- [ ] Add entity resolver (`src/semantics/entity_resolver.py`) — normalize agency/recipient names using config
- [ ] Add metric interpreter (`src/semantics/metric_interpreter.py`) — resolve metric terms using dictionary
- [ ] Add time interpreter (`src/semantics/time_interpreter.py`) — fiscal year/quarter/half rule-based conversion
- [ ] Add scope interpreter (`src/semantics/scope_interpreter.py`) — contracts only, prime only, active only
- [ ] Add ambiguity detector (`src/semantics/ambiguity_detector.py`) — flag unresolvable ambiguity at IR stage

### Pipeline integration
- [ ] Rebuild `src/pipeline.py` — question → IR → prompt → LLM → SQL → execute
- [ ] Update `src/prompt_builder.py` — build prompt from IR, not raw question
- [ ] Add tests for each IR module
- [ ] Add integration test for full IR → SQL pipeline

## Milestone M3 - Validation and Repair

- [ ] Add static schema validator
- [ ] Add metric-definition checks
- [ ] Add time-axis checks
- [ ] Add scope/state checks
- [ ] Add retry / repair loop
- [ ] Add repair success metrics

## Milestone M4 - Policy Layer

- [ ] Add ambiguity router for answer vs clarify vs abstain
- [ ] Add uncertainty scoring
- [ ] Add risky-answer suppression policy
- [ ] Add hard-case memory for repeated failure patterns
- [ ] Add paraphrase robustness checks

## Milestone M5 - Productization and Benchmarking

- [ ] Add CLI entrypoint
- [ ] Add structured logs and traces
- [ ] Add regression CI command
- [ ] Add benchmark report template
- [ ] Add release checklist

## Ordering Rules

1. AC gate must be implemented before M2 coding begins (prevents shortcutting).
2. M2 config/metadata first, then IR modules, then pipeline integration.
3. M3 after M2 pipeline produces real scores.
4. M4 after M3 metrics are visible.
5. M5 is not a substitute for correctness work.
