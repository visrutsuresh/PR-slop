#!/usr/bin/env bash
# Reproduction entrypoint. baseline/advanced are filled in once the problem
# PDF is published at kickoff; eval runs the trivial built-in example so the
# repo is verifiable end to end before the real solution exists.
set -euo pipefail

usage() { echo "usage: $0 {baseline|advanced|eval}" >&2; exit 1; }

[ $# -eq 1 ] || usage

case "$1" in
  baseline)
    echo "[baseline] TODO: run the baseline solution once the problem is published."
    ;;
  advanced)
    echo "[advanced] TODO: run the advanced solution once the problem is published."
    ;;
  eval)
    echo "[eval] running trivial built-in example (pre-kickoff placeholder)"
    python3 test_harness.py
    ;;
  *)
    usage
    ;;
esac
