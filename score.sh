#!/usr/bin/env bash
set -uo pipefail

cd "$(dirname "$0")"

MODE="${1:---quick}"
EXTRA="${2:-}"

# Architecture compliance gate
echo "=== Architecture Compliance ==="
python -m src.eval.architecture_check || AC_FAIL=1
AC_FAIL=${AC_FAIL:-0}
echo ""

# Score
echo "=== Score ==="
case "$MODE" in
  --quick|--full)
    python -m src.eval.score_runner "$MODE" $EXTRA
    ;;
  *)
    echo "Usage: ./score.sh --quick | --full [--stub]" >&2
    exit 2
    ;;
esac

if [ "$AC_FAIL" -eq 1 ]; then
  echo ""
  echo "BLOCKED: Architecture compliance gate failed. Fix violations before merging."
  exit 1
fi
