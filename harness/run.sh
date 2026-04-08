#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCORE_OUT="$($ROOT_DIR/score.sh --quick)"

echo "[harness] quick score"
echo "$SCORE_OUT"

echo
echo "[harness] recommended next action"
echo "1. Read program.md"
echo "2. Read docs/wbs_v0.1.md"
echo "3. Pick the next unchecked WBS item"
echo "4. Make a small change"
echo "5. Re-run ./score.sh --quick"

echo
echo "[harness] suggested ownership order"
echo "- foundation"
echo "- data-eval"
echo "- semantics"
echo "- generator"
echo "- verifier"
echo "- policy"
echo "- bench"
