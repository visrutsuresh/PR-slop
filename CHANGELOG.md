# Improvement Changelog

Each entry: what changed, and the evidence that drove the decision (a trace, a failing test, a
metric, a judge-visible constraint). Filled in from kickoff onward.

## 2026-08-27 — pre-kickoff harness

Built `harness/trace.py`, `test_harness.py`, `run.sh`, and the submission templates before the
problem PDF was published, because agent trajectories cannot be reconstructed after the fact.
Evidence: competition deliverable 4 requires trajectories "from the agent instructions through to
the final result"; without a logger in place before the first real agent run, that run's trajectory
is lost permanently. See `PRE-EXISTING.md`.

<!-- TODO: one entry per meaningful iteration from kickoff onward. -->
