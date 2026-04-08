# Hard-case manifest

Counts by category, tier, and expected behavior:

- metric_ambiguity: 26 cases | answer=13, clarify=13, core=21, extended=5
- time_interpretation: 18 cases | answer=13, clarify=5, core=15, extended=3
- scope_state: 48 cases | answer=29, clarify=19, core=33, extended=15
- entity_resolution: 58 cases | answer=44, clarify=14, core=52, extended=6
- missingness_linked: 31 cases | answer=22, clarify=9, core=25, extended=6
- join_aggregation: 27 cases | answer=22, clarify=5, core=24, extended=3
- easy_baseline: 20 cases | answer=20, core=20, extended=0

Total cases: 228
Core tier: 190 | Extended tier: 38

Gold template entries (answer cases): 163

Use `combined_hard_cases.jsonl` for scoring pipelines.
`--quick` uses core tier only. `--full` uses core + extended.
