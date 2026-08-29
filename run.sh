#!/usr/bin/env bash
# Reproduction entrypoint. harvest fetches the eval set (network, run once
# by the author, its output committed under data/); baseline/advanced are
# filled in once the problem PDF is published at kickoff; eval runs the
# harness + eval-set tests against the committed cache, never the network.
set -euo pipefail

usage() { echo "usage: $0 {harvest|baseline|advanced|eval}" >&2; exit 1; }

[ $# -eq 1 ] || usage

case "$1" in
  harvest)
    echo "[harvest] fetching the eval set via gh api (network, run once, then commit data/)"
    python3 harvest.py
    ;;
  baseline)
    echo "[baseline] TODO: run the baseline solution once the problem is published."
    ;;
  advanced)
    echo "[advanced] TODO: run the advanced solution once the problem is published."
    ;;
  eval)
    echo "[eval] reads only the committed cache under data/, never the network"
    python3 test_harness.py
    python3 test_harvest.py
    python3 baselines/regex_rule.py
    ;;
  *)
    usage
    ;;
esac
