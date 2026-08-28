# micro1 Frontier Engineering Challenge 2026: Submission

<!-- TODO after kickoff: real project name and one-line description. -->

Status: pre-kickoff scaffolding only. The problem PDF (the document that says what to actually build) is published 2026-08-28 15:00 UTC. Nothing below the harness section is filled in yet. See `PRE-EXISTING.md` for what existed before kickoff.

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

`baseline` runs the simple, first-pass solution. `advanced` runs the improved version built on top of it. `eval` runs the checks that confirm both are working. See `docs/reproduction.md` for the full step-by-step guide, written for someone starting from a clean checkout with nothing set up yet.

## Improvement Changelog

See `CHANGELOG.md`. Every meaningful change is logged there with the evidence that drove the next decision (a failing test, a bad result, a judge-visible constraint).

## Main failure mode

<!-- TODO: where does the advanced solution still break, and why. -->

## Hot take

<!-- TODO: one opinionated, defensible claim about the problem or the approach. -->

## Agent instructions

The exact instructions given to each AI agent used in this submission, in the words actually used to prompt it. This satisfies deliverable 1's own wording, "the instructions that shape each agent." This section is the one place those instructions live in full. Each individual run also carries its own copy of the instruction it was given, inside that run's trace file (a trace is the full step-by-step record of what one agent run actually did, saved under `traces/`). That per-run copy is supporting evidence that a real run used these instructions. It does not replace stating them here.

<!-- TODO after kickoff: paste the actual instruction/system-prompt text per agent role used
     (e.g. baseline-agent, advanced-agent). One subsection per agent. -->

## Tools disclosure

Required per the rule book: "You must disclose the tools you used and submit the required trajectories for evaluation." (A trajectory, also called a trace in this repo, is the step-by-step record of everything one agent run did: what it read, what it changed, what it decided, and how it ended.)

| Tool / model | Where used | Notes |
| --- | --- | --- |
| <!-- TODO --> | | |

The trace files themselves live in `traces/`. Each run gets its own readable write-up at `traces/<run_id>.md`. `traces/INDEX.md` lists every run, grouped by agent.

## Harness (pre-existing, see PRE-EXISTING.md)

The harness is the support code built before kickoff, the plumbing that records what each agent does and checks nothing is broken. It contains no logic specific to the actual problem, since the problem was not known yet when it was built.

- `harness/trace.py`: the logger that records every agent run as it happens, strips out anything that looks like a password or API key before saving (see `docs/reproduction.md` for exactly what that redaction step does and does not guarantee), and turns the raw record into the readable trace files described above
- `run.sh`: `baseline` / `advanced` / `eval` entrypoints (the three commands above)
- `test_harness.py`: the harness's own test suite, run with `python3 test_harness.py`
