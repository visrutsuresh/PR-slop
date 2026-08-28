# Pre-Existing Code Declaration

Per rule book item 2: "Make it clear what existed before the competition and what you added."

## What existed before kickoff (2026-08-28 15:00 UTC)

Built 2026-08-27, before the problem PDF was released. Every commit dated before 2026-08-28 15:00 UTC
in this repository's history is part of the pre-kickoff build, verifiable directly via `git log`; none
of them are ever rewritten. That claim is timestamp-based on purpose so it stays true as further
pre-kickoff hardening commits land, rather than naming a fixed commit count that a later commit could
make stale. The commits known at time of writing:

**Commit `f8be460869f94b00a5eb3340cfe8deb0dd2b5753`, 2026-08-27 23:43:54 UTC** — trajectory-logging
infrastructure that cannot be reconstructed retroactively once real agent runs start:
- `harness/trace.py` — trajectory logger (redaction pass, JSONL writer, markdown renderer, trace index)
- `harness/__init__.py` — empty package marker
- `test_harness.py` — plain-assert test suite for the logger
- `.gitignore`, `.dockerignore`
- This file

**Commit `6ab12f8576ea0c1dca76692f94558e97ee269f75`, 2026-08-27 23:45:20 UTC** — reproduction and
submission-template scaffolding:
- `run.sh` — `baseline` / `advanced` / `eval` entrypoints
- `README.md` — submission skeleton (intended user, bottleneck, value, changelog, failure mode, hot
  take, tools disclosure, agent instructions)
- `CHANGELOG.md` — iteration-log template
- `SUBMISSION-CHECKLIST.md` — deliverable-to-file tracking checklist
- `Dockerfile` — plain, generic 4-line image, not adapted from any prior repo
- `docs/video-script.md` — five-minute beat sheet template
- `docs/reproduction.md` — reproduction-guide template

**Commit `633aade`, 2026-08-28 00:09:18 UTC** — closed a pre-kickoff review pass: a connection-URL
credential redaction gap (`scheme://user:password@host` strings), plus its test coverage.

Later pre-kickoff commits continue hardening these same declared files (bug fixes found in review,
e.g. crash-safety on malformed trace lines, ignore-file coverage) with no new problem-specific logic.
See `git log` for the full, current, authoritative list.

Nothing above is adapted from any prior repository. It was written from scratch against the
published rule book and deliverables page, generic to any future problem, with zero
problem-specific logic.

## What gets added after kickoff (2026-08-28 15:00 UTC)

Everything else: the baseline solution, the advanced solution, `harness/compare.py`, any
dependency layers in the Dockerfile, filled-in `docs/reproduction.md` content, and any code adapted
from elsewhere. This section is updated once the problem is known, listing anything reused and its
source.

<!-- POST-KICKOFF: list reused code / sources here -->
