# Pre-Existing Code Declaration

Per rule book item 2: "Make it clear what existed before the competition and what you added."

## What existed before kickoff (2026-08-28 15:00 UTC)

Built 2026-08-27, before the problem PDF (the document describing what to actually build) was released. Every commit dated before 2026-08-28 15:00 UTC in this repository's history is part of the pre-kickoff build. This can be checked directly by anyone by running `git log`, and none of these commits are ever rewritten afterward. This claim is based on the timestamp on purpose, not on a fixed commit count, so it stays true even as later commits keep tightening this same pre-kickoff code (bug fixes, safety hardening) without adding anything specific to the actual problem. The commits known at time of writing:

**Commit `f8be460869f94b00a5eb3340cfe8deb0dd2b5753`, 2026-08-27 23:43:54 UTC**, trajectory-logging
infrastructure that cannot be reconstructed retroactively once real agent runs start:
- `harness/trace.py`, trajectory logger (redaction pass, JSONL writer, markdown renderer, trace index)
- `harness/__init__.py`, empty package marker
- `test_harness.py`, plain-assert test suite for the logger
- `.gitignore`, `.dockerignore`
- This file

**Commit `6ab12f8576ea0c1dca76692f94558e97ee269f75`, 2026-08-27 23:45:20 UTC**, reproduction and
submission-template scaffolding:
- `run.sh`, `baseline` / `advanced` / `eval` entrypoints
- `README.md`, submission skeleton (intended user, bottleneck, value, changelog, failure mode, hot
  take, tools disclosure, agent instructions)
- `CHANGELOG.md`, iteration-log template
- `SUBMISSION-CHECKLIST.md`, deliverable-to-file tracking checklist
- `Dockerfile`, plain, generic 4-line image, not adapted from any prior repo
- `docs/video-script.md`, five-minute beat sheet template
- `docs/reproduction.md`, reproduction-guide template

**Commit `633aade`, 2026-08-28 00:09:18 UTC**, closed a pre-kickoff review pass: a connection-URL
credential redaction gap (`scheme://user:password@host` strings), plus its test coverage.

Later pre-kickoff commits keep hardening these same declared files (bug fixes found during review, for example making the logger survive a broken trace line, or widening what gets ignored by git) without adding anything specific to the actual problem. See `git log` for the full, current, authoritative list.

Nothing above is copied or adapted from any prior repository. It was written from scratch against the published rule book and deliverables page. None of it is specific to this year's problem; it would work the same way for any future one.

## What gets added after kickoff (2026-08-28 15:00 UTC)

Everything else. This paragraph was written before kickoff in the future tense; it is now rewritten against what actually happened.

`harness/compare.py` was planned and **never built**. `scoring.py` does that job, shared by every system so none of them gets a different yardstick. No extra dependencies were added to the Dockerfile: the whole project uses the standard library only. Nothing anywhere is adapted from another repository.

`harvest.py`, `baselines/regex_rule.py`, `baselines/__init__.py`, `test_harvest.py`, and the `harvest` subcommand added to `run.sh`: the evaluation-set harvester, written from scratch after kickoff, against a design that went through three rounds of independent review before any code was written. That review is summarised in `CHANGELOG.md`. Nothing in these files is adapted from any prior repository. `data/cases/`, `data/issues.jsonl`, `data/manifest.json`, and `data/pseudonym_salt.txt` are its committed output, fetched live from `microsoft/vscode` via the authenticated `gh api` CLI.

## Everything else in this repository was written after kickoff

Listed in full, so "what existed before" and "what we added" are both explicit rather than one being left to inference.

| File | What it does |
| --- | --- |
| `agent_v4.py` | The shipped system: four roles and a loop |
| `agent.py`, `agent_v2.py`, `agent_v3.py`, `agent_v5.py`, `agent_v6.py` | The other five agent versions, kept so the six-version table can be recomputed |
| `triage.py` | The product, the page a maintainer reads, and the single-submission view |
| `retriever.py` | The search over the project's recorded problems |
| `evidence.py` | The evidence card and the second-opinion list |
| `run_baseline.py` | The simple comparison version |
| `run_advanced.py` | The intermediate two-stage version |
| `scoring.py` | Shared scoring for every system |
| `task_spec.py` | The task description handed identically to every system |
| `isolation_probe.py` | Proves the model cannot reach the answers |
| `versions.py` | Recomputes the six-version table |
| `check_docs.py` | Fails if a published number stops matching the code |
| `build_traces.py`, `build_agent_traces.py` | Render the step-by-step records |
| `data/responses/` | Every answer every system gave, 120 files |
| `docs/explainer.html`, `docs/versions.html` | Plain-language explanations of the problem and the six versions |
| `CHANGELOG.md` content | Every entry after the pre-kickoff harness entry |

The `traces/` records themselves are generated output, not hand-written.

**How to check any of this yourself.** `git log --reverse` shows the order everything was built, and every commit before 2026-08-28 15:00 UTC is pre-kickoff. No commit in this repository has been rewritten.
