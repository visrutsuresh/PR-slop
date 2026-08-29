# Reproduction Guide

Written for someone starting from a clean environment (a fresh machine or container with nothing from this project already set up) who has never seen this repo before. Filled in once the problem is known. The harness section below already works today.

## Clean environment

- macOS/Linux, Python 3.12 (the version used inside the Docker container, from `Dockerfile`'s `python:3.12-slim` base image, not necessarily the Python version already on your own machine, which may be different).
- No third-party Python packages required to run the harness itself. Only the Python standard library is used.

## Setup

```bash
git clone <repo-url>
cd PR-slop
<!-- TODO: any solution-specific setup, e.g. pip install -r requirements.txt -->
```

## Exact commands

```bash
./run.sh harvest      # network, gh api, re-fetches the eval set (skips if data/cases/ already has 15 cases; already committed, so you normally never need this)
./run.sh baseline   # <!-- TODO: describe what this runs -->
./run.sh advanced    # <!-- TODO: describe what this runs -->
./run.sh eval         # runs the harness's own test suite plus the harvested eval-set tests plus the leak baseline; runs the solution's own eval once written. Never touches the network: reads only the committed cache under data/ (ground rule 10)
```

## Data required

The evaluation set (15 `microsoft/vscode` pull requests, balanced 5/5/5 across the three buckets, plus a supporting issue corpus) is fetched once by `harvest.py` and committed under `data/`: `data/cases/pr-<n>.json` (one per case, `input` + `truth`), `data/issues.jsonl` (the retrieval corpus), `data/manifest.json` (exact queries, the re-derived bucket census, the pinned source commit, out-of-repo exclusions), and `data/pseudonym_salt.txt`. A fresh clone already has all of this; `./run.sh harvest` only re-runs the fetch if it is missing (or with `--force`), and requires `gh` authenticated with public read scope.

## Expected output

Today: `./run.sh eval` runs `test_harness.py` (10 `PASS` lines, `10/10 passed`), then `test_harvest.py` (14 `PASS` lines, `14/14 passed`), then `baselines/regex_rule.py` (prints the leak baseline's balanced accuracy, currently 0.667).
<!-- TODO: expected output of baseline/advanced once written. -->

## How trace redaction actually works (read this before sharing any trace file)

Every agent run is logged as a trace: the full step-by-step record of what that run did, saved under `traces/`. Before anything is written to disk, the logger runs a redaction pass that looks for common shapes of API keys, passwords, and tokens (things like `sk-...`, `AKIA...`, GitHub tokens, JWTs, PEM private key blocks, and any `key=value` pair whose key name looks like a secret) and replaces the matched part with `[REDACTED]`.

This is real protection, but it is defense in depth, not a guarantee. It catches the credential shapes this project has actually seen come up during a build; it does not catch every possible shape a secret could take, and it cannot catch a secret sitting in plain unstructured text with no recognizable prefix or key name attached to it. Never assume a trace file is fully clean just because it went through this pass. Review a trace yourself before it leaves the machine, especially before it goes into a public repository. Once submitted, this repository becomes micro1's permanent property, so this check matters more here than it would for a throwaway local log.

## Versions

- Container Python: 3.12 (`python:3.12-slim`)
- <!-- TODO: any pinned solution dependencies -->

## Approximate runtime and cost

- `./run.sh eval` (harness + harvest tests + leak baseline): under 1 second, $0, no API calls, reads only the committed cache.
- `./run.sh harvest` (only needed if `data/` is missing or `--force`): a few minutes, roughly 450-500 `gh api` calls, well inside GitHub's authenticated 5,000/hour rate limit, $0 (no LLM calls).
- <!-- TODO: baseline/advanced runtime and API cost once written. -->
