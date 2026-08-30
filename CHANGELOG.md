# Improvement Changelog

Each entry: what changed, and the evidence that drove the decision (a trace, a failing test, a metric, a judge-visible constraint). Filled in from kickoff onward.

## 2026-08-27: pre-kickoff harness

Built `harness/trace.py`, `test_harness.py`, `run.sh`, and the submission templates before the problem PDF (the document describing what to actually build) was published. This was done first because a trajectory, the full step-by-step record of what an agent run actually did, cannot be put together after the fact. It has to be captured live, while the run is happening. Evidence: competition deliverable 4 requires trajectories "from the agent instructions through to the final result." Without a logger already running before the first real agent run, that run's trajectory would be lost for good. See `PRE-EXISTING.md`.

## 2026-08-29: evaluation-set harvest

Built `harvest.py`, `baselines/regex_rule.py`, `test_harvest.py`, and wired a `harvest` subcommand into `run.sh`. Gated by contrarian plan-review PASS at loop 3 of 3 (change_id `prslop-harvest-2026-08-29`), which found and fixed 7 binding conditions before any code was written, most importantly: `created_at` was still in the allow-list and turned out to be an 8x to 30x open-duration leak in disguise (86.2% AUC, removed); the frozen closing-reference pattern did not actually capture owner/repo, so the cross-repo carve-out could not have worked; a third declaration form (`owner/repo#N`) was missing from the pattern; `changed_files` and `patch` are not obtainable from the raw pull object as originally written (`changed_files` there is an integer count, not a file list).

Evidence from the real harvest run: the frozen pattern re-derives the bucket census as 23/54/23 on the true 100-most-recently-closed pull requests, against the earlier, narrower rule's 15/74/11 (condition E; both numbers are in `data/manifest.json`). The no-model reference rule that reads the (now-stripped) declared-link field directly scores 66.7% balanced accuracy by construction (`baselines/regex_rule.py`), which is the size of the leak the strip closes. All 15 harvested cases pass the allow-list, forbidden-field, and zero-surviving-match tests (`test_harvest.py`, 14/14), including the positive control that at least one case's redacted reference used the URL or shorthand form and not just bare `#N`.

## Baseline, the starting point

**What we tried and why.** One direct prompt per pull request, no tools, no way to search the project's reported problems, no way to read the source. This is micro1's own first suggested baseline. We chose it over a cleverer one on purpose: it is simple because they named it simple, not crippled to make our own system look good.

**Result on the fifteen cases.** Balanced accuracy **33.3%**. The floor for three equal piles is 33.3%. So the simple version performs exactly as well as guessing.

Per-pile recall was 0.20, 0.40, 0.40. It declined to answer on 5 of 15, which is the honest behaviour we asked for. It wrongly called 1 of 10 merged items "not merged". Cost 1.84 USD across the fifteen.

**Decision.** This is the number to beat. Recorded as the starting point.

## A measurement mistake we made and corrected, before it reached the report

**What happened.** The first scoring run said the simple version scored **86.7%** on citing real evidence. That looked like it had contradicted a prediction we had written down in advance, which was that a system with no repository access would invent references.

It had not contradicted it. We were counting the wrong thing.

**The evidence.** Of its thirteen "valid" citations, **twelve were file paths copied straight out of the case it had just been handed**. Quoting back a path you were given is not evidence of anything. It required no access and no lookup.

Only three citations were issue numbers, which genuinely cannot be known without checking the project. **Two of those three did not exist.**

**What we changed.** Citations are now counted in two groups: free ones, meaning a file path already present in that case's own input, and real ones, meaning an issue number that must be looked up. The headline rate uses real ones only. Under that measure the simple version scores **1 of 3**, and the original prediction stands.

**What it taught us.** A metric that a system can satisfy by echoing its own input is not measuring the system. We caught this only because the result looked too good and we checked what was underneath it. That is now a standing check on every number in this project: before publishing a figure, ask what the cheapest way to score well on it would be.

## Stage 1, search the project's reported problems

**What we tried and why.** The simple version scored exactly as well as guessing. It had no way to answer the question that decides the first pile: does this work fix something someone already reported? There are 403 reported problems in our saved copy, far too many to paste into one prompt, so answering that means going and searching.

Added a plain word-overlap search, weighting rare words higher so a query does not simply match whichever entry is longest, and dividing by length so a very long entry does not win on volume alone. No clever model, no index, nothing installed.

**Evidence it works.** Across the nine cases that really do reference a reported problem, the search puts the correct one **first 78% of the time and in the top eight 89% of the time**.

**Decision.** Kept. The eight best matches are put in front of the model, with an explicit instruction that they may be irrelevant and not to cite one anyway if none fits.

## Stage 2, check every claim before trusting it

**What we tried and why.** The thing a maintainer actually fears is not a wrong label, it is a confident claim that turns out to be invented. The simple version demonstrated exactly that: of three reported problems it named, two did not exist. So every reference our system produces is resolved against the real project, and anything that does not exist is struck out rather than shown. If a first-pile verdict rested entirely on a reference that turned out to be made up, the verdict is downgraded to "cannot determine", because the evidence for it is gone.

**Evidence.** Here is the honest part. **The check struck nothing. Zero references removed across all fifteen cases.**

**Decision. Kept, but we are not claiming it earned its place on this evidence.** It fired zero times, so on these fifteen cases it contributed nothing measurable. The reason it had nothing to catch is that stage 1 handed the model real reported problems to work from, so it no longer needed to invent any. That is a genuine effect, but it is stage 1 getting the credit, not stage 2.

We keep it for two reasons and state them plainly. It costs nothing to run. And the failure it guards against is documented, in this very project, in the simple version's own output. A guard that has not yet fired is not the same as a guard that is not needed. But anyone reading our numbers should know that on this evidence, stage 1 did the work.

## Result

| Measure | Simple version | Our system | Change |
| --- | --- | --- | --- |
| Balanced accuracy | 33.3% | **73.3%** | +40.0 points |
| Per-pile recall | 0.20 / 0.40 / 0.40 | 1.00 / 1.00 / 0.20 | |
| Merge-worthy work wrongly rejected | 1 of 10 | **0 of 10** | |
| Reported problems named that really exist | 1 of 3 (33%) | **9 of 9 (100%)** | |
| Declined to answer | 5 of 15 | 0 of 15 | |
| Cost across 15 cases | 1.84 USD | 1.88 USD | +0.04 |

The floor for three equal piles is 33.3%, so the simple version performed exactly as well as guessing.

**Where our system still fails, stated rather than buried.** It catches only **1 of 5** not-merged items. It is good at recognising work that was accepted and poor at recognising work that was not. Given that finding the not-merged pile is the entire point of the tool, this is the real limitation and no amount of headline accuracy hides it.

The likely reason is in our own evaluation design, and we wrote it down before running anything: "not merged" on this project mostly does not mean bad work. Most of that pile is automated housekeeping or maintainers closing their own work in favour of another approach. Our system reads those as real contributions, because they are.

## The full agent, built and then REMOVED

**What we tried and why.** A fair criticism of everything above is that it is a script, not an agent. Search runs once, a model is asked once, a check runs over the answer. Nothing ever decides anything.

So we built the real thing. Four roles, and a loop:

- an **investigator** that writes its own search wording, reads the results, and can search again with different words if the first attempt was poor
- a **claim checker** that reads the actual source at the pinned commit and tests whether the submission does what it says, rather than trusting the description
- an **adjudicator** that decides the pile using what the other two found
- a **verifier** that, when a claim does not hold up, **sends the work back** for another attempt instead of quietly deleting it

This is genuinely agentic. The agent chose 8 follow-up searches on its own across the 15 cases. Its claim checker read real source for 14 of 15.

**Result: it is worse. Much worse.**

| | Two-stage version | Full agent |
| --- | --- | --- |
| Balanced accuracy | **73.3%** | 46.7% |
| Merge-worthy work wrongly rejected | **0 of 10** | 4 of 10 |
| Cost for 15 cases | **1.88 USD** | 6.75 USD |

It broke five cases the simpler version had right, and fixed one.

**Why, precisely.** This is not noise, it has a mechanism, and we found it.

The claim checker judged three submissions as "the code does not support the claim". In all three the adjudicator moved them to pile 3, not merged. **All three had in fact been merged by the maintainer.**

The claim checker may even have been correct about the code. It did not matter. The maintainer merged the work anyway.

**What it taught us, and this is the real lesson of the project.** We had already written down that "not merged" does not mean "bad work". Then we built a system whose whole extra capability is judging whether work is good, and wired that judgement into predicting whether it was merged. We conflated the exact two things our own evaluation design says are different.

Giving an agent a sharper sense of code quality made it WORSE at this task, because the task is not about quality. Every extra reasoning step pulled it further toward answering a question nobody asked.

**Decision: REMOVED.** The two-stage version ships. The agent is kept in the repository at `agent.py`, runnable, with its 15 saved responses, so anyone can reproduce this negative result.

**What we would keep from it.** The investigator's habit of writing its own search wording is good, and it works: it produced queries like "snippet tab stop limit 10 nested placeholders" from a title that said none of those things, using the words a person REPORTING a problem would use rather than the words a developer FIXING it would use. That idea is worth carrying into a future version. The quality judgement is not.

**Honest note on the verifier.** It sent nothing back across all 15, so the loop we built never actually ran. Twice now, across two architectures, our verification stage has fired zero times. That is worth saying plainly rather than describing a mechanism that has never once been exercised.

## The reframe: stop predicting the human, start producing evidence

**The problem with everything above, and it was the CEO who named it.**

Every version so far predicts what a maintainer did. That contains a flaw we could not argue away: **if a maintainer overlooks something valuable and closes it, and the tool correctly says the work is good, we mark the tool wrong.** The scoring fights the product. A tool built this way can never help with the failure a maintainer would most want help with.

It is not hypothetical. The single case that no version out of six ever got right, pr-308696, is exactly that shape: real code, fixing a genuinely reported problem, confirmed against the actual source, closed anyway. Six versions all said "this is good work". We scored all six as mistakes.

**What we changed.** We kept the merge prediction, honestly labelled as what it is, a prediction of a human decision. Alongside it we now produce an **evidence card**: claims that are true or false against the repository, with no human verdict involved.

| Claim | How it is checked |
| --- | --- |
| Names a genuinely reported problem | the number resolves in the project |
| Names real files | the paths are really in this change |
| Carries tests | the change touches test paths |
| Substantive | line and file counts, not a trivial edit |
| Description matches the code | the claim checker read the real source |

Nobody labels anything. Each is a fact.

**Result on the 15 cases.** Of 16 factual claims the agent made, **16 hold up, 100%**. Eleven of fifteen submissions carry tests. Fourteen are substantive.

**The disagreement report, which is the actual point.** When the evidence says a submission is well supported and the record says it was closed, that is not the tool being wrong. That is the tool finding work a human may have overlooked. Two surfaced:

- **pr-308696**, "Close non-dirty editors when cancelling Close All Editors". Fixes genuinely reported problem #305306, code confirmed against the real source, 44 lines. Closed without merging.
- **pr-324044**, "Report when buffered events are flushed to a late listener". Code confirmed, carries tests, 99 lines across 7 files. Closed without merging.

The case that was our worst failure is now the headline output.

## A counting error I made in this very file, caught before publishing

The first run of the evidence card reported **61.5%** of factual claims holding up. That contradicted the 100% reported elsewhere, so we checked instead of publishing it.

The bug: "named no problem at all" was being counted as "named a problem that does not exist". Ten of fifteen submissions named none, and all ten were being scored as false claims.

**This is the exact error this project pre-registered a rule against**, in writing, before any system was run: zero offered is not zero percent correct. We wrote the rule, published it, and then broke it in a new file two days later. The real figure is 16 of 16.

Recorded rather than quietly fixed, because the lesson is the useful part: writing a rule down does not make you follow it. The thing that caught this was a number looking wrong next to another number, not discipline.

## The product, built against a stated goal

**Why this came last, which was a mistake.** Everything before this improved a number without a stated product. That is how version 5 happened: a change that sounded obviously right, made with no picture of what it was for, cost 27 points.

**The goal, written down before building.** A maintainer opens their queue, runs one command, and gets a single page: what to read first and why, the normal middle, what to leave, and separately anything closed that probably should not have been. Every claim points at something real. Nothing is touched.

Done means four things: one command, every factual claim resolves, it never acts, and a maintainer would behave differently for having read it. We had the first three and not the fourth. We produced scores for a judge, not a page for a person.

**Three passes, then stop.** The stopping rule was fixed in advance, because version 5 proved that past a point this becomes tuning noise.

**Pass 1.** Built the page. It worked and it was incoherent: the same submission appeared under "read these first" and again under "closed, worth a second look". A closed item has no business in an open queue.

**Pass 2.** Closed items now appear only in the second-opinion section. Text cut at word boundaries instead of mid-word, which had made the page look unfinished. File paths shortened to the last two segments so the layout holds.

**Pass 3.** Removed a number I had invented. The page said "roughly 31 minutes of reading", computed from three minutes plus one per file, a formula with no basis in anything. **This project had already dropped a human-time metric once for exactly that reason, and I reintroduced it an hour later.** Replaced with counts that are simply true: files and lines. Added the pull request links, since a maintainer wants to open the thing.

**Verified after.** Every reported problem named on the page resolves against the repository. Five named, zero fake.

**The honest count of made-up numbers in this project: three.** The 86.7% citation figure, the 61.5% evidence figure, and the invented minutes. Each was caught, each is recorded. The pattern is worth more than any single fix: every one came from producing a number that felt reasonable rather than one that was measured, and every one was caught by a human or a machine noticing it sat oddly beside another number. Writing a rule against it did not prevent the second and third.

## A leak that survived the first scrub, found by auditing every tracked file

**What happened.** An audit of all 224 tracked files for personal addresses found one still present: a `Co-authored-by:` line with a real address, inside the **body** of one case.

**Why the first fix missed it.** The scrub ran on patches only. Titles and bodies were never scrubbed, because the leak we found first happened to be in a patch and we fixed exactly what we saw.

**Two reasons it mattered**, even though the address belongs to a bot. The README claims no contributor identity survives anywhere, and that claim was simply false. And "Co-authored-by: Copilot" tells the model the work was machine-assisted, which is the kind of hint that can quietly correlate with the outcome we are trying to predict.

**What we did.** Extended the scrub to titles and bodies, re-applied it, then **regenerated that case for all three systems**, so the committed input still matches the answers that produced our published numbers. Every score is unchanged: baseline 33.3%, script 73.3%, agent 73.3% with the same per-pile shape.

**The test now checks the whole input**, not just the patch, and it is proven to fail on a planted address in a body.

**The pattern, which is the useful part.** This is the third leak of the same family: the declaration in a body, then identity in a patch, now identity in a body. Each time we fixed precisely the surface where the leak was found and did not ask where else that class could live. The thing that caught this one was not a test we wrote. It was walking every tracked file and asking what a hostile reader would grep for.
