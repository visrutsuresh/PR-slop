# micro1 Frontier Engineering Challenge 2026 — Submission

<!-- TODO after kickoff: real project name and one-line description. -->

Status: pre-kickoff scaffolding only. The problem PDF is published 2026-08-28 15:00 UTC. Nothing
below the harness section is filled in yet. See `PRE-EXISTING.md` for what existed before kickoff.

## Intended user

<!-- TODO: who is this for? Be specific, not "developers". -->

## Their current bottleneck

<!-- TODO: what makes this painful today, without this project? -->

## Why solving it is valuable

<!-- TODO: what changes for the intended user once this exists? -->

## Quickstart

```bash
./run.sh baseline
./run.sh advanced
./run.sh eval
```

See `docs/reproduction.md` for the full reproduction guide.

## Improvement Changelog

See `CHANGELOG.md`. Every meaningful iteration is logged there with the evidence that drove the
next decision.

## Main failure mode

<!-- TODO: where does the advanced solution still break, and why. -->

## Hot take

<!-- TODO: one opinionated, defensible claim about the problem or the approach. -->

## Tools disclosure

Required per the rule book: "You must disclose the tools you used and submit the required
trajectories for evaluation."

| Tool / model | Where used | Notes |
| --- | --- | --- |
| <!-- TODO --> | | |

Agent trajectories: `traces/`. Rendered per-run markdown at `traces/<run_id>.md`, index at
`traces/INDEX.md`.

## Harness (pre-existing, see PRE-EXISTING.md)

- `harness/trace.py` — trajectory logger used by every agent run in this submission
- `run.sh` — `baseline` / `advanced` / `eval` entrypoints
- `test_harness.py` — `python3 test_harness.py`
