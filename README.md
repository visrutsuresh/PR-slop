# PR-slop

**Triage for maintainers buried in AI-generated pull requests.** Give it a queue of open pull requests; it returns a sorted worklist in three buckets, act now, worth reviewing, safe to prune, where every claim carries a citation checked against the real repository.

Submission for the **micro1 Agentic Workflows Hackathon 2026**. Kickoff 2026-08-28 15:00 UTC, submissions close 2026-08-31 18:00 UTC.

Status: problem locked, evaluation design fixed, build in progress. See `PRE-EXISTING.md` for exactly what existed before kickoff.

## Intended user

A solo or small-team maintainer of a popular public repository. Unpaid, no triage staff, and every low-effort submission costs them the same first read as a genuine one.

## Their current bottleneck

They personally read every incoming pull request, verify its claims by hand, and search their own issue history to see whether it duplicates something already filed. There is no filter in front of them.

The volume is documented, not assumed. Daniel Stenberg has said the curl project is "effectively being DDoSed" by AI-generated bug reports, roughly 20% of its 2025 submissions were AI slop, and OCaml maintainers rejected a single AI-generated pull request of 13,000 lines.

## Why solving it is valuable

The maintainer stops reading the prune pile. That is the whole proposition. If they cannot trust bucket 3 enough to skip it, nothing has been saved no matter how good the accuracy number looks.

### The cause is upstream, and it is a hiring incentive

Most write-ups of this problem stop at "maintainers are tired". The more useful observation is why the slop exists at all.

Job descriptions ask candidates for evidence of open source contribution. Students and career switchers who want that line on a CV are therefore pushed toward contribution VOLUME rather than contribution VALUE, and generative tools make volume nearly free. The slop is not vandalism. It is a rational response to a hiring signal.

Two job postings collected first-hand during the author's own internship search, quoted verbatim:

- Chubb, AI Apprentice, desirable criteria: "Contribution to open-source AI projects"
- Singtel, AI Product Manager Builder Intern: "Public portfolio, hackathon wins, open-source contributions"

The author is not a maintainer and does not claim to be. He is the person standing under the pressure that produces the slop, which is why this framing is first-hand rather than researched.

## Quickstart

```bash
./run.sh baseline
./run.sh advanced
./run.sh eval
```

`baseline` runs the simple, first-pass solution. `advanced` runs the improved version built on top of it. `eval` runs the checks that confirm both are working. See `docs/reproduction.md` for the full step-by-step guide, written for someone starting from a clean checkout with nothing set up yet.

## How it works

Four stages, built incrementally, each one added only after a measurement showed it was needed.

1. **Retriever.** Fetches the pull request, the repository's contributing guidelines, and searches the existing issue corpus for near-duplicates and for the issue this pull request may be addressing.
2. **Claim checker.** Pulls out each factual assertion in the submission ("this crashes on empty input") and checks it against the actual source.
3. **Adjudicator.** Weighs the retrieved evidence into a bucket and a disposition.
4. **Verifier.** A separate pass that resolves every citation against the real repository and downgrades anything that does not resolve to "cannot determine".

**Multi-agent, but NOT autonomous.** It performs no consequential action of any kind. It never posts, comments, closes, merges or labels anything on any real repository. It writes a report and a human decides. Closing a real contributor's pull request affects a real person, so a qualified human reviewer stays in the loop by design.

There is also a single-pull-request mode, because real reviewers work sequentially. It is deliberately NOT part of the evaluation: single-item triage is close to what one prompt already does, and scoring it would misrepresent where the system's value actually is.

## Evaluation

**Repository:** `microsoft/vscode`. Verified before use: of the 100 most recent closed pull requests, 15 fall in bucket 1, 74 in bucket 2, 11 in bucket 3, so all three buckets clear a 5-case floor. It was preferred over `home-assistant/core` because it rejects more pull requests (11 per 100 against 4), and rejected pull requests are the class this tool exists to find.

**Cases:** 15, sampled DELIBERATELY to 5 per bucket. Random sampling would have skewed to bucket 2, which is 74% of recent closed pull requests.

**Where the answer key comes from.** No maintainer ever records "this pull request was high value", so the answer key is built from what the maintainer actually DID:

| What the maintainer did | Bucket |
| --- | --- |
| Merged it, and it closed a linked issue | 1, act now |
| Merged it, no linked issue | 2, worth reviewing |
| Closed it without merging | 3, prune |

The agent sees each pull request with every outcome signal stripped out, as though it had just arrived, and predicts a bucket. The baseline gets the identical cases and the identical output format.

**Known limits of that answer key, stated up front.** Merge decisions carry social and political factors unrelated to technical quality, so this is a proxy for value, not truth. It is also survivorship-flavoured: a good pull request that sat ignored and was auto-closed as stale is filed under "prune", so the system is marked wrong for correctly calling it good.

**Baseline.** A single direct prompt with basic instructions, given the pull request text, with NO repository access. This is micro1's own first suggested baseline. Declared resource difference: the agent has repository access and the baseline does not, because repository access is precisely the intervention being measured. A stronger keyword-search baseline was considered and was out of scope for the time available.

**Pre-registered targets, frozen before any evaluation was run.** False-prune rate under 10%, since that is the error that destroys the product's value. Citation validity at 90% or higher. Both were fixed in advance and are not revised in light of results.

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
