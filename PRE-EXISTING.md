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

Everything else: the simple first-pass solution (the "baseline"), the improved solution built on top of it (the "advanced" solution), `harness/compare.py` (which will score the two against each other), any extra dependencies added to the Dockerfile, the filled-in content of `docs/reproduction.md`, and any code adapted from elsewhere. This section gets updated once the problem is known, listing anything reused and where it came from.

<!-- POST-KICKOFF: list reused code / sources here -->
