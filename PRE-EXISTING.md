# Pre-Existing Code Declaration

Per rule book item 2: "Make it clear what existed before the competition and what you added."

## What existed before kickoff (2026-08-28 15:00 UTC)

Built 2026-08-27, before the problem PDF was released, as trajectory-logging infrastructure that
cannot be reconstructed retroactively once real agent runs start:

- `harness/trace.py` — trajectory logger (redaction pass, JSONL writer, markdown renderer, trace index)
- `harness/__init__.py` — empty package marker
- `test_harness.py` — plain-assert test suite for the logger
- `.gitignore`, `.dockerignore`
- This file

Nothing above is adapted from any prior repository. It was written from scratch against the
published rule book and deliverables page, generic to any future problem, with zero
problem-specific logic.

The first commit in this repository's history is dated before kickoff and is the machine-verifiable
timestamp for this declaration. That commit is never rewritten.

## What gets added after kickoff (2026-08-28 15:00 UTC)

Everything else: the baseline solution, the advanced solution, `harness/compare.py`, any
dependency layers in the Dockerfile, filled-in `docs/reproduction.md` content, and any code adapted
from elsewhere. This section is updated once the problem is known, listing anything reused and its
source.

<!-- POST-KICKOFF: list reused code / sources here -->
