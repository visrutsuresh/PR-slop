# PR-slop

**Triage for maintainers buried in AI-generated pull requests.** Give it a queue of open pull requests; it returns a sorted worklist in three buckets, act now, worth reviewing, not merged, where every claim carries a citation checked against the real repository.

Submission for the **micro1 Agentic Workflows Hackathon 2026**. Kickoff 2026-08-28 15:00 UTC, submissions close 2026-08-31 18:00 UTC.

Status: problem locked, evaluation design fixed, build in progress. See `PRE-EXISTING.md` for exactly what existed before kickoff.

## Intended user

A solo or small-team maintainer of a popular public repository. Unpaid, no triage staff, and every low-effort submission costs them the same first read as a genuine one.

## Their current bottleneck

They personally read every incoming pull request, verify its claims by hand, and search their own issue history to see whether it duplicates something already filed. There is no filter in front of them.

The volume is documented, not assumed. Daniel Stenberg has said the curl project is "effectively being DDoSed" by AI-generated bug reports, roughly 20% of its 2025 submissions were AI slop, and OCaml maintainers rejected a single AI-generated pull request of 13,000 lines.

## Why solving it is valuable

The maintainer reads the not-merged pile **LAST instead of first**, and can trust that merge-worthy work rarely lands there. That is the proposition, and it is deliberately narrower than "skip that pile entirely".

We do not claim the stronger version, because our own data contradicts it. See the bucket-3 note below: most of what lands there is real work, not slop, so promising a maintainer they can skip it unread would be dishonest. The honest claim is triage ORDERING.

### The cause is upstream, and it is a hiring incentive

Most write-ups of this problem stop at "maintainers are tired". The more useful observation is why the slop exists at all.

Job descriptions ask candidates for evidence of open source contribution. Students and career switchers who want that line on a CV are therefore pushed toward contribution VOLUME rather than contribution VALUE, and generative tools make volume nearly free. The slop is not vandalism. It is a rational response to a hiring signal.

Two job postings collected first-hand during the author's own internship search, quoted verbatim:

- Chubb, AI Apprentice, desirable criteria: "Contribution to open-source AI projects"
- Singtel, AI Product Manager Builder Intern: "Public portfolio, hackathon wins, open-source contributions"

The author is not a maintainer and does not claim to be. He is the person standing under the pressure that produces the slop, which is why this framing is first-hand rather than researched.

## Quickstart

```bash
./run.sh triage      # the product: one page a maintainer reads
./run.sh baseline    # the simple comparison version
./run.sh script      # the intermediate two-stage version
./run.sh agent       # the shipped system, four roles with a loop
./run.sh eval        # the checks
```

All of these replay from committed responses. No account, no network, no cost. See `docs/reproduction.md` for the full step-by-step guide, written for someone starting from a clean checkout with nothing set up yet.

## How it works

Four roles, and a loop. Each was added only after a measurement showed it was needed; the six versions and their numbers are in `CHANGELOG.md`.

1. **Investigator.** Decides for itself what to search for, reads what comes back, and can search again with different wording if the first attempt was poor. It chose 6 follow-up searches on its own across the 15 cases. This is the one choosing the action, not us.
2. **Claim checker.** Reads the actual source at a pinned commit and tests whether the submission does what it says. It ran against real source on 10 of 15.
3. **Adjudicator.** Decides the pile from what the other two found.
4. **Verifier.** Checks every claim and, when one does not hold up, **sends the work back** rather than deleting it quietly.

**Why this is not one prompt.** The project has 403 recorded problems, far too many to hand a model at once, so answering "does this fix something already reported" requires going and searching. The investigator writes those searches itself, which produced queries like `snippet tab stop limit 10 nested placeholders` from a title containing none of those words, because a person reporting a problem uses different words from a developer fixing it.

**Multi-agent, but NOT autonomous.** It performs no consequential action of any kind. It never posts, comments, closes, merges or labels anything on any real repository. It writes a page and a human decides. Closing a real contributor's pull request affects a real person, so a qualified human reviewer stays in the loop by design.

**Single-submission mode**, because real reviewers work through a queue one at a time:

```
./run.sh triage 308696
```

It prints that submission's evidence card, the suggested pile, and a second-look note if the evidence is strong but it was closed. It is deliberately NOT part of the evaluation: judging one item in isolation is close to what a single prompt already does, and scoring it would misrepresent where the value is.

## Evaluation

**Repository:** `microsoft/vscode`. Repo selection was verified before use against a 15/74/11 split under an earlier, narrower label rule (`home-assistant/core` was the alternative, rejecting fewer pull requests, 4 per 100 against vscode's double-digit rate). **Re-derived at harvest time under the FROZEN pattern actually shipped (`harvest.py`), because a published number must be one the project's own rule reproduces:** of the true 100 most-recently-closed pull requests as of the harvest run, **23 fall in bucket 1, 54 in bucket 2, 23 in bucket 3** (see `data/manifest.json` -> `census_re_derived`). All three buckets still clear the 5-case floor comfortably, and no decision changes.

**Cases:** 15, sampled DELIBERATELY to 5 per bucket. Random sampling would have skewed to bucket 2, which is 74% of recent closed pull requests.

**Where the answer key comes from.** No maintainer ever records "this pull request was high value", so the answer key is built from what the maintainer actually DID:

| What the maintainer did | Bucket |
| --- | --- |
| Merged it, and it DECLARED a closing link to an issue | 1, act now |
| Merged it, no DECLARED closing link | 2, worth reviewing |
| Closed it without merging | 3, not merged |

The agent sees each pull request as an allow-list of five fields (number, title, body, changed-file list, patch), with the closing reference redacted, and predicts a bucket. Source reads are pinned to a commit predating the case window, because reading live `HEAD` would itself reveal whether a pull request was merged.

**Known bias we did not fix, stated here rather than left for a reader to find.** Every bucket-1 target issue is guaranteed present in our corpus by seeding. Bucket-2 cases have no declared target to seed, so their real counterparts are present only by chance. "Found a strong topical match" therefore correlates with bucket 1 by construction, which flatters the act-now versus worth-reviewing split inside our bucket-accuracy figure. Fixing it properly would need hand-labelling, which would make the evaluation circular. So we disclose it instead. The baseline gets the identical cases and the identical output format.

**Bucket 3 is NOT a slop detector, stated plainly.** "Not merged" is a workflow fact the API records for free. It is not a quality judgment. Of 17 `microsoft/vscode` bucket-3 pull requests inspected before building the eval set, 4 were bots and roughly 10 were team members closing their own real work, one of them over 7,700 added lines, in favour of another approach. Only ONE resembled AI slop. If the agent correctly calls an insider's real refactor "real work, do not deprioritise it", the oracle still grades that bucket 3. That is a disclosed proxy error, not a system failure.

**Sampling rule.** At least 3 of the 5 bucket-3 cases are non-bot, outside-contributor closes (bot: `user.type == "Bot"` or a verified automation account; outside contributor: `author_association` is `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR` or `NONE`). This deliberately skews the sample away from the true bucket-3 population, where bots and insiders are the majority.

The unfiltered breakdown, measured on all 23 bucket-3 pull requests in the same census window above: **4 bots, 5 insiders, 14 outside-contributor closes.** The curated 5 (the actual eval cases): **1 bot, 1 insider, 3 outside-contributor closes**, the minimum the sampling rule allows. So the eval set is deliberately more outsider-heavy than the true population, and that skew is disclosed here rather than hidden. (This mechanical bot/insider/outsider split is measured directly from `author_association` and is separate from the smaller, human-read 17-case spot check above, which judges AI-slop content, not authorship.)

**Author identity is removed, and here is the honest version of why.** Before building anything we checked whether a rule using no model at all could already sort the piles. Using the declared reference plus whether the author is a project insider, it scores **53.3%**. Using the author alone, it scores **40.0%**, against a floor of 33.3% for three equal piles.

Two things must be said plainly about those figures. First, an earlier draft of this file published 78% and 50%. Those came from a different, larger sample taken before the evaluation set existed, and they are **withdrawn**. The numbers above are computed on the exact fifteen cases in `data/cases/`, and anyone can recompute them.

Second, 40.0% against a 33.3% floor is a difference of about one case at this sample size, so it argues very little on its own. We are not going to pretend it is strong evidence. The stronger reason for removing author identity is not the score, it is that publishing real contributors' names and mail addresses alongside a label saying their work was not merged is not something we are willing to do.

**A defect we found in our own data and fixed, recorded rather than quietly patched.** The first version of this evaluation set left every contributor's real name and mail address inside the code changes, in all fifteen cases, while this file claimed the system never sees who submitted a pull request. That claim was false. One case also still contained the giveaway phrase the strip exists to remove. Both are fixed, the scrub is deterministic and re-runnable, and the tests now check for both.

**Stripping includes the declared closing reference, not just the merge outcome.** The bucket label is a deterministic function of that field, so leaving it visible would let the agent read the label off the input instead of earning it. For the pull requests that declare a link, and every bucket-1 case does by definition, this makes the input less realistic than what a maintainer actually sees. That is a disclosed trade, not a free one.

**Known limits of that answer key, stated up front.** Merge decisions carry social and political factors unrelated to technical quality, so this is a proxy for value, not truth. It is also survivorship-flavoured: a good pull request that sat ignored and was auto-closed as stale is filed under "not merged", so the system is marked wrong for correctly calling it good.

**Baseline.** A single direct prompt with basic instructions, given the pull request text, with NO repository access. This is micro1's own first suggested baseline. Declared resource difference: the agent has repository access and the baseline does not, because repository access is precisely the intervention being measured. A stronger keyword-search baseline was considered and was out of scope for the time available.

**Pre-registered targets, frozen before any evaluation was run.** False-prune rate under 10%, where a false prune means the system predicted "not merged" for something the maintainer actually merged. Citation validity at 90% or higher. Both were fixed in advance and are not revised in light of results.

**We cannot actually demonstrate the false-prune threshold at this sample size, and we say so rather than let a reader assume otherwise.** The denominator is 10 cases. Even a perfect 0 of 10 gives a 95% upper confidence bound of about 26%, so "under 10%" is unfalsifiable in the passing direction here. The pre-registration still earns its place as anti-goalpost-moving discipline, but the result is reported with its bound, never as a bare pass.

**Resolution limit.** One flipped case moves balanced accuracy by 6.7 points. Two systems within about two cases of each other are not distinguishable by this evaluation.

**Contamination, precisely.** The harvest window postdates the model's training cutoff, so memorisation of these specific pull requests is genuinely mitigated. What recency does not mitigate is identity-level priors: the model knows the vscode maintainer roster from pretraining. That is why author identity is pseudonymised and removed from the input entirely.

## Improvement Changelog

See `CHANGELOG.md`. Every meaningful change is logged there with the evidence that drove the next decision (a failing test, a bad result, a judge-visible constraint).

## Main failure mode

**It is good at spotting work that was accepted and poor at spotting work that was not.** It catches 1 of 5 not-merged items, against 5 of 5 on both merged piles.

That is the wrong way round for a tool whose purpose is finding the pile you can safely leave until last, and we are not going to dress it up. Overall accuracy of 73.3% hides it, which is why the per-pile numbers are printed next to it everywhere.

The cause is visible in our own evaluation design and we wrote it down before running anything. On this project "not merged" mostly does not mean poor work. Of seventeen such pull requests we inspected, four were automated housekeeping and about ten were maintainers closing their own real work in favour of another approach. Our system reads those as genuine contributions, because they are genuine contributions. It is being marked wrong for being right about the work and wrong about the outcome.

## Hot take

**DRAFT. Confirm against the real 15-case results before finalising.**

"Closed without merging" looks like it should mean "rejected as low quality". On `microsoft/vscode` it mostly does not. Of 17 such pull requests inspected while building this eval set, 4 were bots doing routine housekeeping, roughly 10 were the vscode team closing their OWN large and real work in favour of a different approach, one case being a refactor of over 7,700 added lines, and only 1 looked like actual AI slop.

The practical lesson: any triage system built from GitHub's free mechanical metadata, merged or not, linked issue or not, is measuring maintainer BEHAVIOUR, not maintainer JUDGMENT of quality. That is enough to build and evaluate a working system. It is not the same claim as "this detects AI slop". Detecting slop specifically would need a narrower, probably human-labelled oracle.

Anyone reproducing a maintainer-behaviour triage tool on a different repository should expect the same gap and disclose it the same way, rather than assuming their own repo's bots and insiders average out to the label they hoped to measure.

## Agent instructions

The exact instructions given to each AI agent used in this submission, in the words actually used to prompt it. This satisfies deliverable 1's own wording, "the instructions that shape each agent." This section is the one place those instructions live in full. Each individual run also carries its own copy of the instruction it was given, inside that run's trace file (a trace is the full step-by-step record of what one agent run actually did, saved under `traces/`). That per-run copy is supporting evidence that a real run used these instructions. It does not replace stating them here.

### The task description, given word for word to BOTH sides

This is the whole of it. The simple version and our system receive this identical text, so the measured difference reflects what the systems can reach, not how hard we tried on the wording. It lives in one file, `task_spec.py`, for exactly that reason.

```
You are triaging a pull request for a busy open source maintainer.

Sort it into exactly one of three buckets:

  1 = act now.          Work worth merging, and it addresses a problem someone
                        had already reported in the project.
  2 = worth reviewing.  A genuine contribution that needs a human read, with no
                        indication it answers an already-reported problem.
  3 = not merged.       You judge the maintainer would not merge this. Note this
                        covers several different things: routine automated
                        housekeeping, work superseded by another approach, a
                        duplicate, or low-effort or machine-generated filler.

Bucket 3 is NOT a quality verdict on the contributor. It means you judge this
did not become part of the codebase.

You may also answer 0 = cannot determine, if the evidence does not support a
call. Answering 0 is preferred over guessing.

Reply with JSON only, no prose around it, in exactly this shape:

{"bucket": 1|2|3|0,
 "confidence": "high"|"medium"|"low",
 "reason": "one or two sentences",
 "citations": ["#12345", "src/path/to/file.ts"]}

Rules for "citations":
  - Cite only things you can actually point at: issue numbers as #NNNNN, or
    file paths.
  - If you have no way to check the repository, return an EMPTY list. Do not
    invent an issue number or a file path to fill the field. An empty list is
    a correct answer and is scored as such.

```

Each case then appends that pull request's title, description, list of changed files, and code changes.

### What our system adds, and only our system

After the text above, our system appends the eight closest matches from searching the project's 403 saved reported problems, under this instruction:

> These were found by searching the project. They may or may not be what this pull request answers. Judge for yourself. If one of them is genuinely what this work fixes, cite it as #NNNNN and use it to support bucket 1. If none of them really matches, say so and do NOT cite one anyway.

The simple version receives no such section, because having no way to search the project is precisely the thing being measured.

### The instruction added to every call, both sides

> You answer with JSON only. No preamble, no markdown fences.

## The experiment we removed

We also built the fully agentic version: an investigator that writes its own search wording and can search again, a claim checker that reads the real source and tests the submission's claims, an adjudicator, and a verifier that sends failed work back to be redone.

**It scored 46.7%, against 73.3% for the simpler two-stage version, and it wrongly rejected merge-worthy work 4 times out of 10 instead of zero.** It cost three and a half times as much.

The reason is precise. Its claim checker judged three submissions as not supported by their own code. The adjudicator moved all three to the not-merged pile. **All three had actually been merged.** The claim checker may well have been right about the code; the maintainer merged the work regardless.

We had already written down that "not merged" does not mean "bad work". Then we built a system whose extra ability is judging whether work is good, and used it to predict whether work was merged. Sharper judgement of quality made it worse, because the task is not about quality.

It is removed from the shipped solution and kept at `agent.py`, runnable, with its saved responses, so the negative result reproduces.

## Judging the work, not the decision

Everything above predicts what a maintainer did. That has a flaw worth stating loudly: **if a maintainer overlooks something valuable and closes it, and this tool correctly calls the work good, our scoring marks the tool wrong.**

The one case no version ever got right, pr-308696, is very likely exactly that. Real code, fixing a genuinely reported problem, confirmed against the actual source, closed anyway.

So alongside the prediction we produce an **evidence card**, made only of claims that are true or false against the repository, with no human verdict involved: does it name a genuinely reported problem, does it name real files, does it carry tests, is it substantive, does the code match its description.

Of 16 factual claims the agent made across the 15 cases, **16 hold up**.

**The disagreement report is the point.** Well-supported work that was closed anyway is not the tool failing. It is the tool finding something a human may have missed. Run `python3 evidence.py` and it surfaces two, including pr-308696.

## Results

Three systems, same 15 cases, same model, same instructions.

| Measure | Simple version | Intermediate script | **Shipped agent** |
| --- | --- | --- | --- |
| Balanced accuracy | 33.3% | 73.3% | **73.3%** |
| Pile 1 / 2 / 3 recall | 0.20 / 0.40 / 0.40 | 1.00 / 1.00 / **0.20** | 0.60 / 0.80 / **0.80** |
| Merge-worthy work wrongly rejected | 1 of 10 | 0 of 10 | **0 of 10** |
| Reported problems named that exist | 1 of 3 | 9 of 9 | **5 of 5** |
| Cost across 15 cases | 1.86 USD | 1.88 USD | 4.14 USD |

The floor for three equal piles is 33.3%, so **the simple version scored exactly as well as guessing.**

**Read the two 73.3% figures carefully, because they are not the same thing.** The intermediate script reaches that number by being uniformly generous: perfect on both accepted piles, and **0.20** on the not-merged pile. It finds one in five of the pile you actually wanted to stop reading. The agent finds **four in five** of it, while still never binning good work.

Tied on the headline. Four times better at the job.

**What fifteen cases can and cannot tell you.** One case moves balanced accuracy by 6.7 points, so two systems within about two cases of each other are not distinguishable here. The 40-point gap over guessing is well clear of that; the tie between the script and the agent is not a real tie in shape, but it IS a real tie in headline and we are not going to claim otherwise. The false-rejection figure is weaker still: 0 out of 10 carries a 95% upper bound of about 26%, so we **cannot** demonstrate our pre-registered "under 10%" at this sample size, and we do not claim to have.

**Citations are counted in two groups on purpose.** A file path copied out of the case the system was just handed is free and proves nothing. Only a reported-problem number, which cannot be known without checking, is informative. The table uses those only. Counting both together is what produced a misleading 86.7% in our first scoring pass, written up in the changelog.

## Tools disclosure

Required per the rule book: "You must disclose the tools you used and submit the required trajectories for evaluation."

| Tool / model | Where used | Notes |
| --- | --- | --- |
| `claude-sonnet-5` | Both the simple version and ours | Same model on both sides, so the comparison measures the system and not the model. Recorded in every saved response and checkable from them. |
| Claude Code, non-interactive | How the model is called | Run from an empty folder outside this project with file reading, searching, shell, web access, editing and sub-agents all switched off. See `isolation_probe.py`. |
| `gh` command line | Collecting the fifteen cases, once | Its output is committed under `data/`. Nothing else needs it. |
| Python standard library only | Everything else | No packages installed. |

**Why the isolation matters.** Our first attempt asked the model, running normally inside this project, to report the recorded answer for one case. **It opened the answer file and returned the correct value.** Left alone, the simple comparison version could have read the answers instead of reasoning, making the whole comparison worthless. `isolation_probe.py` now has to pass before anything is generated, and it must reply that it has no way to read a file.

The trace files live in `traces/`, 45 records, one per run of each system, listed in `traces/INDEX.md`.

The shipped agent's records are marked **captured**: it writes each step as the run happens, so what you read is the live record. The other two are marked **reconstructed**, because their calls were saved whole and replayed into the same format afterwards. Nothing in a reconstructed record is invented, every field comes from a committed file, but the distinction is stated rather than glossed.

## Harness (pre-existing, see PRE-EXISTING.md)

The harness is the support code built before kickoff, the plumbing that records what each agent does and checks nothing is broken. It contains no logic specific to the actual problem, since the problem was not known yet when it was built.

- `harness/trace.py`: the logger that records every agent run as it happens, strips out anything that looks like a password or API key before saving (see `docs/reproduction.md` for exactly what that redaction step does and does not guarantee), and turns the raw record into the readable trace files described above
- `run.sh`: `baseline` / `advanced` / `eval` entrypoints (the three commands above)
- `test_harness.py`: the harness's own test suite, run with `python3 test_harness.py`
