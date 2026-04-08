#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

MODE="${1:---quick}"
EXTRA="${2:-}"

case "$MODE" in
  --quick|--full)
    python -m src.eval.score_runner "$MODE" $EXTRA
    ;;
  *)
    echo "Usage: ./score.sh --quick | --full [--stub]" >&2
    exit 2
    ;;
esac
