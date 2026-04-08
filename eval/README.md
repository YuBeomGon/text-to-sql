# Evaluation Pack

This folder contains the first concrete evaluation assets for the public NL2SQL project.

## What is included

- `cases/*.jsonl`
  - 300 semantic hard cases across the six primary failure axes
- `cases/combined_hard_cases.jsonl`
  - combined manifest for downstream scoring and filtering
- `cases/gold_result_snapshot_template.jsonl`
  - template to freeze positive-case gold outputs after the dataset slice is locked
- `expansions/*.yaml`
  - expansion templates for paraphrase, temporal fuzz, and adversarial ambiguity

## Why semantic cases first

The original task's failure modes are primarily semantic rather than syntactic:
- wrong metric meaning
- wrong time interpretation
- wrong scope or status filter
- entity matching failure
- missingness / business-rule failure
- join or aggregation failure

At this stage, semantic cases let the team evaluate:
- policy behavior (`answer`, `clarify`, `abstain`)
- semantic interpretation quality
- verifier coverage
- regression of previously understood failure modes

## Case schema

Each JSONL row contains:
- `case_id`
- `category`
- `polarity`
- `expected_behavior`
- `difficulty`
- `query`
- `tags`
- `expected_semantics`
- `notes`

`expected_semantics` is intentionally structured to support planner-level and verifier-level evaluation before exact result snapshots are available.

## How to use this pack

1. Use the semantic cases immediately for unit, integration, and regression testing.
2. Lock a concrete USAspending slice.
3. Execute the gold SQL or reviewed reference plan for each positive case.
4. Save the output hash / canonical result into `gold_result_snapshot_template.jsonl`.
5. Promote the most important cases into the locked quick/full score sets.

## Recommended promotion path

- quick score: 24-40 locked cases
- full score: 120-180 locked cases
- semantic regression pack: full 300-case semantic manifest
