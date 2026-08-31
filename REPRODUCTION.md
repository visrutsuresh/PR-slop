# Reproduction guide

Written for someone starting from nothing, with no account of any kind.

## The short version

```bash
git clone https://github.com/visrutsuresh/PR-slop
cd PR-slop
./run.sh triage      # the product: one page a maintainer reads
./run.sh eval        # checks
./run.sh baseline    # the simple version's numbers
./run.sh script      # the intermediate two-stage version
./run.sh agent       # the shipped system's numbers
./run.sh evidence    # judges the work rather than the decision, plus the
                     #   second-opinion list of well-supported work that was
                     #   closed anyway
./run.sh triage 308696   # one submission, for a reviewer working one at a time
```

That is everything. **No account, no key, no payment, no internet.** Those commands reproduce every number in the README exactly.

## What you need

Python 3.10 or newer. Nothing else. No packages are installed, nothing is downloaded, and the standard library is all that is used.

**On the Dockerfile.** One sits in the repository, from the pre-kickoff scaffolding. It copies the project into `python:3.12-slim` and runs the checks. We are not claiming it works, because Docker was not running on the machine this was finished on and we did not verify it. It is a convenience, not a requirement: the project needs nothing but Python, so running the commands directly is the supported path and the one we tested.

## Why nothing needs an account

Every model answer this project ever received is saved whole, under `data/responses/`, and committed. The commands above read those saved answers and recompute the results from them.

This is deliberate, and it is the only honest way to do it. **These models are not repeatable.** Ask one the same question twice and the wording differs. So if you re-ran the models yourself, you would get different text, possibly different verdicts, and numbers that do not match our README, through no fault of either of us. The saved answers are the record. Recomputing from them gives the same result every time, for anyone.

The competition organisers supply no accounts or credits, so every entrant faces this. We solved it by making verification need nothing.

## What you should see

```
=== baseline, one direct prompt, no repository access ===
balanced accuracy : 33.3%   per-bucket ['0.20', '0.40', '0.40']
false prune       : 1/10 merged items called not-merged
citations, free   : 12 file paths copied from the case's own input
citations, real   : 1/3 issue numbers exist (33.3%)
declined to call  : 5/15

=== the agent: investigate, check, decide, verify ===
balanced accuracy : 73.3%   per-bucket ['0.60', '0.80', '0.80']
false prune       : 0/10 merged items called not-merged
citations, real   : 5/5 issue numbers exist (100.0%)
searches decided  : 21 rounds across 15 cases (6 the agent chose itself)
claims tested     : 10/15 against the real source
```

Note the two 73.3% figures are not the same system. The intermediate script
(`./run.sh script`) reaches it by being uniformly generous, scoring 0.20 on the
pile you actually want to skip. The shipped agent scores 0.80 there.

Roughly two seconds each. No cost.

## What the data is

Fifteen closed pull requests from `microsoft/vscode`, all public, collected once and committed under `data/`.

- `data/cases/` : the fifteen. Each has an `input` half, which is all a system is allowed to see, and a `truth` half, the answer.
- `data/issues.jsonl` : 403 reported problems from the same project, the thing our system searches.
- `data/manifest.json` : when it was collected, the exact queries used, the pile counts, and the pinned commit.
- `data/responses/` : every model answer, saved whole.
- `traces/` : a readable step-by-step record for each of the 45 runs.

## Checking that we are not cheating

The strongest reason to distrust an evaluation like this is that the system might be reading the answers rather than working them out. We nearly had exactly that problem.

An early check asked the model, running normally inside this project folder, to report the recorded answer for one case. **It opened the file and gave the correct answer.** So every model call now runs from an empty folder outside the project, with file reading, searching, shell access, web access, editing and sub-agents all switched off.

You can rerun that check:

```bash
./run.sh probe
```

It must print `PASS` and the model must say it has no way to read a file. If it ever prints the answer instead, nothing generated afterwards can be trusted.

You can also confirm the answers never leaked into the questions:

```bash
python3 tests/test_harvest.py
```

Fifteen checks. Among them: the input half contains exactly five permitted fields and nothing else, no contributor name or email survives anywhere, and no giveaway phrase pointing at the answer survives. That last set exists because an earlier version of this project failed all three, which is written up in `IMPROVEMENT-CHANGELOG.md`.

## If you want to run the models yourself

```bash
REGENERATE=1 ./run.sh baseline
REGENERATE=1 ./run.sh agent
```

This needs Claude Code installed and signed in. **Expect different numbers.** That is the models being unrepeatable, not a fault. The isolation check runs first and refuses to continue if it fails.

Recollecting the fifteen cases needs the GitHub command line tool and will produce a **different set entirely**, because it takes the most recently closed pull requests and that list moves daily:

```bash
REGENERATE=1 ./run.sh harvest
```

## Using it from your own assistant, over MCP

The repository carries a project-scoped `.mcp.json`, so an MCP-aware assistant started in this directory picks the server up with no setup:

```
cd PR-slop
claude          # the pr-slop server is offered automatically
```

If your client needs an explicit registration instead:

```
claude mcp add pr-slop -- python3 /absolute/path/to/src/mcp_server.py
```

Then ask in plain language. Three tools are exposed:

| Tool | Needs | Cost |
| --- | --- | --- |
| `whats_new` | nothing, reads the local memory store | **free, offline, instant** |
| `triage_pull_request` | `gh` authenticated, the model | about 0.55 USD |
| `triage_queue` | `gh` authenticated, the model | about 0.45 USD per submission |

**Start with `whats_new`.** It costs nothing and tells you whether anything changed since the last triage, which on a quiet day is the whole answer.

**Driving it without an assistant.** It speaks newline-delimited JSON-RPC 2.0 on stdin and stdout, so you can exercise it from a shell and see exactly what a client would see:

```
printf '%s\n' \
 '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
 '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
 '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
 | python3 src/mcp_server.py
```

Expect the handshake, then the three tool definitions. `./run.sh mcp` runs the same server and prints the registration line first. Running it by hand and seeing it wait is correct: it is reading stdin, not hanging.

**No install step, deliberately.** No MCP SDK exists here. The transport is written against the standard library. This section does not introduce the project's first dependency, and it does not put an install wall in front of the offline reproduction above.

**It cannot act.** The tools read, and they write one HTML file. No merge, no close, no comment, no label.

## Cost and time, measured not estimated

| | Simple version | Intermediate script | Shipped agent |
| --- | --- | --- | --- |
| Fifteen cases | 1.86 USD | 1.88 USD | 4.14 USD |
| Per case | about 0.12 USD | about 0.13 USD | about 0.28 USD |

The agent costs more because it makes several calls per submission rather than
one. The investigator plans a search and then judges the results, the claim
checker reads real source, and the adjudicator decides. The whole thing can go
round again if the verifier rejects a claim.

Verifying from the saved answers costs nothing and takes seconds.
