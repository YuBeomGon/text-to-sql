#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

MODE="${1:---quick}"

case "$MODE" in
  --quick|--full)
    python -m src.eval.score_runner "$MODE"
    ;;
  *)
    echo "Usage: ./score.sh --quick | --full" >&2
    exit 2
    ;;
esac
