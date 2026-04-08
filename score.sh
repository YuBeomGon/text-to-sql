#!/usr/bin/env bash
set -euo pipefail

MODE="${1:---quick}"

print_quick() {
  cat <<'TXT'
Score breakdown (quick - core tier only):
  eval_tier:                 core (190 cases)
  execution_success:         TODO
  positive_result_accuracy:  TODO
  negative_abstain_f1:       TODO
  metric_definition:         TODO
  time_axis:                 TODO
  scope_state:               TODO
  entity_resolution:         TODO
  easy_baseline:             TODO
  repair_success:            TODO
  latency_score:             TODO

Total: TODO
Gates:
  schema_grounding: TODO
  execution_success: TODO
  risky_answer_rate: TODO
TXT
}

print_full() {
  cat <<'TXT'
Score breakdown (full - core + extended tiers):
  eval_tier:                 core (190) + extended (38) = 228 cases
  execution_success:         TODO
  positive_result_accuracy:  TODO
  negative_abstain_f1:       TODO
  metric_definition:         TODO
  time_axis:                 TODO
  scope_state:               TODO
  entity_resolution:         TODO
  easy_baseline:             TODO
  repair_success:            TODO
  latency_score:             TODO

Total: TODO
Gates:
  schema_grounding: TODO
  execution_success: TODO
  risky_answer_rate: TODO
TXT
}

case "$MODE" in
  --quick)
    print_quick
    ;;
  --full)
    print_full
    ;;
  *)
    echo "Usage: ./score.sh --quick | --full" >&2
    exit 2
    ;;
esac
