# Reproduction Guide

Written for someone starting from a clean environment. Filled in once the problem is known;
the harness section below already works.

## Clean environment

- macOS/Linux, Python 3.12 (the container version, from `Dockerfile`'s `python:3.12-slim` base —
  not necessarily the local interpreter version, which may differ).
- No third-party Python packages required for the harness itself (stdlib only).

## Setup

```bash
git clone <repo-url>
cd micro1-frontier-2026
<!-- TODO: any solution-specific setup, e.g. pip install -r requirements.txt -->
```

## Exact commands

```bash
./run.sh baseline   # <!-- TODO: describe what this runs -->
./run.sh advanced    # <!-- TODO: describe what this runs -->
./run.sh eval         # runs the harness's own test suite today; solution eval once written
```

## Data required

<!-- TODO: what input data/fixtures the solution needs, and where they come from. -->

## Expected output

Today: `./run.sh eval` prints 6 `PASS` lines and `6/6 passed`.
<!-- TODO: expected output of baseline/advanced once written. -->

## Versions

- Container Python: 3.12 (`python:3.12-slim`)
- <!-- TODO: any pinned solution dependencies -->

## Approximate runtime and cost

- Harness test suite: under 1 second, $0 (no API calls).
- <!-- TODO: baseline/advanced runtime and API cost once written. -->
