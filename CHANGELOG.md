# Improvement Changelog

Each entry: what changed, and the evidence that drove it. Every number below is recomputable from the committed answers; `./run.sh versions` rebuilds the central table.

**How to read this.** The arc, in one paragraph, so the detail has somewhere to sit.

A simple prompt scored **33.3%**, exactly the same as guessing. Adding search over the project's recorded problems took a script to **73.3%**. The fully agentic version was then built and was **worse, 46.7%**, for a reason we could point at. Six rebuilds followed, two of which we broke ourselves, ending at **73.3%** with four times the script's ability to find the pile that matters. Along the way the evaluation itself turned out to be flawed, because it scores the tool against what a human decided, so we added a second output that judges the work instead.

**Six entries record us being wrong**, and they are the ones worth reading: a removed experiment that cost 27 points, three published figures that turned out to be invented, a data leak that survived its own fix twice, an overclaim in the first sentence of the README, a claim about our own live run that the run's own record contradicts, and an ordering rule the code had been applying backwards. None were found by a test we had written in advance.

## 2026-08-27: pre-kickoff harness

Built `harness/trace.py`, `test_harness.py`, `run.sh`, and the submission templates before the problem PDF (the document describing what to actually build) was published. This was done first because a trajectory, the full step-by-step record of what an agent run actually did, cannot be put together after the fact. It has to be captured live, while the run is happening. Evidence: competition deliverable 4 requires trajectories "from the agent instructions through to the final result." Without a logger already running before the first real agent run, that run's trajectory would be lost for good. See `PRE-EXISTING.md`.

## 2026-08-29: evaluation-set harvest

Built `harvest.py`, `baselines/regex_rule.py`, `test_harvest.py`, and wired a `harvest` subcommand into `run.sh`. Gated by contrarian plan-review PASS at loop 3 of 3 (change_id `prslop-harvest-2026-08-29`), which found and fixed 7 binding conditions before any code was written, most importantly: `created_at` was still in the allow-list and turned out to be an 8x to 30x open-duration leak in disguise (86.2% AUC, removed); the frozen closing-reference pattern did not actually capture owner/repo, so the cross-repo carve-out could not have worked; a third declaration form (`owner/repo#N`) was missing from the pattern; `changed_files` and `patch` are not obtainable from the raw pull object as originally written (`changed_files` there is an integer count, not a file list).

Evidence from the real harvest run: the frozen pattern re-derives the bucket census as 23/54/23 on the true 100-most-recently-closed pull requests, against the earlier, narrower rule's 15/74/11 (condition E; both numbers are in `data/manifest.json`). The no-model reference rule that reads the (now-stripped) declared-link field directly scores 66.7% balanced accuracy by construction (`baselines/regex_rule.py`), which is the size of the leak the strip closes. All 15 harvested cases pass the allow-list, forbidden-field, and zero-surviving-match tests (`test_harvest.py`, 14/14), including the positive control that at least one case's redacted reference used the URL or shorthand form and not just bare `#N`.

## Baseline, the starting point

**What we tried and why.** One direct prompt per pull request, no tools, no way to search the project's reported problems, no way to read the source. This is micro1's own first suggested baseline. We chose it over a cleverer one on purpose: it is simple because they named it simple, not crippled to make our own system look good.

**Result on the fifteen cases.** Balanced accuracy **33.3%**. The floor for three equal piles is 33.3%. So the simple version performs exactly as well as guessing.

Per-pile recall was 0.20, 0.40, 0.40. It declined to answer on 5 of 15, which is the honest behaviour we asked for. It wrongly called 1 of 10 merged items "not merged". Cost 1.86 USD across the fifteen.

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

**Evidence.** Here is the honest part. **The check struck 0 of 15. Not one reference removed across the whole set.**

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
| Cost across 15 cases | 1.86 USD | 1.88 USD | +0.04 |

The floor for three equal piles is 33.3%, so the simple version performed exactly as well as guessing.

**Where our system still fails, stated rather than buried.** It catches only **1 of 5** not-merged items. It is good at recognising work that was accepted and poor at recognising work that was not. Given that finding the not-merged pile is the entire point of the tool, this is the real limitation and no amount of headline accuracy hides it.

The likely reason is in our own evaluation design, and we wrote it down before running anything: "not merged" on this project mostly does not mean bad work. Most of that pile is automated housekeeping or maintainers closing their own work in favour of another approach. Our system reads those as real contributions, because they are.

## The full agent, built and then REMOVED

**What we tried and why.** A fair criticism of everything above is that it is a script, not an agent. Search runs once, a model is asked once, a check runs over the answer. Nothing ever decides anything.

So we built the real thing. Four roles, and a loop:

- an **investigator** that writes its own search wording, reads the results, and can search again with different words if the first attempt was poor
- a **claim checker** that reads the actual source at the pinned commit and tests whether the submission does what it says, rather than trusting the description
- an **adjudicator** that decides the pile using what the other two found
- a **verifier** that, when a claim does not hold up, **sends the work back** for another attempt instead of quietly deleting it. Across the shipped run it fired once in fifteen; in the earlier two-stage version the equivalent check fired zero times

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

## Six versions of the agent, including two I broke myself

The agent was removed above at 46.7%. Rather than leave it there, it was rebuilt six times, each version changing exactly one thing so the effect could be attributed. Every version's saved answers are committed under `data/responses/`.

| Version | What changed | Score | Piles 1 / 2 / 3 | Good work wrongly binned |
| --- | --- | --- | --- | --- |
| Simple script | (for comparison) | 73.3% | 1.00 / 1.00 / **0.20** | 0 of 10 |
| v1 | first real agent, four roles | 46.7% | 0.40 / 0.60 / 0.40 | **4 of 10** |
| v2 | told it a code judgement is not a merge judgement | 46.7% | 0.40 / 0.60 / 0.40 | 1 of 10 |
| v3 | must commit to a pile; given the true base rate | 73.3% | 0.60 / 1.00 / 0.60 | 1 of 10 |
| **v4** | **fixed the handover between roles** | **73.3%** | 0.60 / 0.80 / **0.80** | **0 of 10** |
| v5 | made the investigator's verdict binding | 46.7% | 1.00 / 0.20 / 0.20 | 0 of 10 |
| v6 | investigator rates its own certainty | 66.7% | 0.80 / 0.80 / 0.40 | 1 of 10 |

**v2, the fix that worked and did not help.** Wrong rejections fell from 4 to 1. The headline did not move, because it stopped rejecting and started shrugging: three answers of "cannot tell", which score as wrong.

**v3, the biggest single jump, and it was not cleverness.** Two changes. It must commit to a pile, because a sorting tool that refuses to sort leaves the maintainer reading everything. And it was told a true fact it had never been given: roughly nine in ten closed submissions on this project were merged. It had been treating the three piles as equally likely, so every flicker of doubt pushed work into reject. 46.7 to 73.3.

**v4, and the finding worth carrying elsewhere.** Two defects, both found by reading the run records rather than guessing at wording. The investigator's conclusion reached the adjudicator as a bare number with no framing, so the adjudicator ignored it. And the investigator was discarding correct matches for not being worded closely enough. **Both were handover failures. Every role behaved sensibly on its own; the system still got the answer wrong because information was lost between them.**

**v5, my own overcorrection, kept because it is the most instructive result here.** I told the adjudicator to accept the investigator's conclusion. It fell from 73.3 to **46.7**. The cause: I had loosened the investigator in v4 so it accepts near-matches, then in v5 made it the final word. Loose plus binding means nearly everything lands in one pile. Pile 1 went to a perfect 1.00 and the other two collapsed to 0.20. A change that sounded obviously right cost 27 points.

**v6, and where we stopped.** Letting the investigator grade its own certainty recovered to 66.7%, still below v4. We stopped there. One case is worth 6.7 points on fifteen, and six attempts against the same fifteen answers is the point where a better number stops indicating a better system. Continuing would have produced a nicer figure and a worse tool.

**Decision: v4 ships, and the argument is not the headline.** It ties the simple script at 73.3%. But it catches **0.80 of the not-merged pile against the script's 0.20**, four times better at the one job the tool exists to do, while matching the script's zero wrongly-binned good work. The script earns its 73.3% by being uniformly generous, which is useless for finding the pile you want to skip.

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

## A guard against the thing that kept going wrong

Three separate times the documents drifted from the code. The README described the wrong system. Then it published the wrong per-pile figures. Then it quoted a cost that had changed when one case was regenerated. Each time a human reading carefully was the only thing that caught it.

`check_docs.py` now runs inside `./run.sh eval`. It reads what the code actually prints for all three systems, accuracy, per-pile recall and cost, and fails if any of it is missing from the README.

It is deliberately dumb: no parsing of our prose, just "does this number appear". That is enough, because all 3 drifts so far were a number that silently stopped being true, not an argument that stopped being valid.

It caught 2 more the moment it was switched on: the per-pile figures and the costs, both stale in the README after one case was regenerated.

## An overclaim in the first sentence, caught by testing our own headline

The README opened with "every claim carries a citation checked against the real repository". Checked against the runs: the agent cited nothing at all on 4 of 15 submissions.

The accurate version is narrower and, we think, better: **every citation it does give you resolves**, and where it has no evidence it says nothing rather than inventing a reference. Five reported problems named, five real, four silences.

Worth noting how this was found. We took the strongest sentence in the document and asked whether the data supported it, rather than waiting for a reader to do that. That is now the last check before anything ships: read your own headline as a hostile reviewer would.

## A metric whose label did not match what it counted

`claims tested : 10/15 against the real source` implied the claim checker only reached source on two thirds of submissions, and the README repeated it.

Checking the run records: **it read real source on all fifteen.** On five it returned "cannot tell" rather than a yes or no. The counter was measuring "reached a definite verdict" and calling it "reached the source". Those are different things, and the label understated a capability while sounding like a limitation.

Relabelled in every version of the agent and corrected in the README. The honest version is also the better one: it reads the source every time, and where the code does not settle the question it says so instead of guessing.

**Fifth time now** that a number in this project meant something other than what it was labelled. The others: a citation rate counting free self-quotes, an evidence rate counting silence as a lie, an invented reading time, and a verifier capability stated without its frequency. The common thread is never arithmetic. It is a label written once, early, and then trusted.

## From evaluation to tool: live open pull requests, and a page instead of terminal text

**The gap, named by the CEO.** "A real tool that maintainers are willing to use isn't a script and terminal text, and it should show them the open PRs, not the closed ones already."

Both halves were right, and together they were the difference between an evaluation wearing a product's clothes and something a person would actually run.

**Why everything until now used closed submissions.** Because that is the only place answers exist. You cannot score a system against pull requests nobody has decided on yet. That constraint shaped the whole project and it was the correct call for measuring, but it meant the tool had never once been pointed at the thing it exists for.

**`./run.sh live owner/repo`** fetches the pull requests actually waiting on any repository, pulls that project's recorded problems to search, and runs the same four roles. Nothing about the system changed. What changed is what it is aimed at.

**Run against the real `microsoft/vscode` queue, five open submissions:**

- **#333399** was correctly linked to reported problem **#333395**, a live link that did not exist when this project started
- **zero invented references** across all five
- 145 seconds, 2.28 USD

**And a page instead of terminal text.** `report.py` writes a self-contained HTML file: no server, no build step, no internet. Three design rules, each from a real constraint. Every claim carries its evidence beside it, because a triage tool a maintainer cannot audit is one they stop trusting after the first wrong call. Anything unconfirmed is shown as unconfirmed rather than quietly dropped. And nothing is ever presented as a decision.

**What the page says about its own limits**, in the footer, because a maintainer deserves to read it before they trust the order: *it does not know your roadmap, your release schedule, or that you already decided against an approach. Those are the reasons good work gets closed, and it cannot see any of them.*

**No score is claimed here and none will be.** Open submissions have no answer to check against. Inventing an accuracy figure for the live tool would be the sixth mislabelled number in this project, and the previous five are already written up above.

## Deciding how much is worth reading today, and pointing at one submission

Two gaps the CEO found in the live tool.

**"How does it decide how many go in each pile?"** It did not. Each submission is judged on its own, so the piles are whatever falls out. With eight open pull requests that is fine. Point it at a busy repository with two hundred and the first pile could hold sixty, which is the original problem with extra steps.

Fixed without touching the model. Within each group, submissions are ordered by how much CHECKED evidence supports them: a confirmed link to a reported problem, then a confirmed description, then tests, then size. **Size ranks last deliberately.** A large diff is work, not value, and ranking by it would reward the exact thing this tool exists to filter. **Corrected later:** this ordering rule is withdrawn, both the tests-and-size keys and the "size ranks last" claim about the code, under the section "Size never ranked last, it ranked first" below, which states the key that actually ships.

Then a cap: only the strongest few per group are marked as today's reading, 5 and 8. The rest sit behind one click, still ordered. **Nothing is hidden.** A hidden submission is one nobody ever looks at again, which is the harm we are trying to prevent, so collapsing is as far as we go.

**"It should be able to be pointed at a specific open one."** `./run.sh live owner/repo 333418`. Verified against a live open submission: 54 seconds, 0.30 USD, its own page. A reviewer working a queue by hand wants this far more often than the whole list.

## The live tool was destroying the author's own evidence before the model saw it

`./run.sh live` reused the evaluation's scrub wholesale. That scrub removes the
author's declared closing reference, and it removes it for a good reason: on a
CLOSED submission the declaration IS the answer key, so leaving it in would let
the agent read its own label off its own input.

An open queue has no answer to protect. There, the same field is the strongest
evidence on the page, because it is a statement by the person who wrote the
code rather than something a model inferred. We were deleting it and then
binning the submission for having no evidence of a link.

Measured on the eight-submission run of 2026-08-30 20:01 UTC: **three of eight
submissions declared a reference and all three were destroyed** (#333390
declared #231076, #333399 declared #333395, #333404 declared #330410; all three
are real open issues).

A run writes its record to `reports/` (`live.py`), and this repository tracks
nothing in there except the one example page, so that run would have left
nothing to check. A reduced copy of its record is therefore
committed at `data/live-record-prefix.json`: every field kept is verbatim, with
the raw GitHub objects, the submission bodies and the patches removed, because
those carry contributor identity this project does not publish. In it, all
three of those submissions carry an empty `problems` list, and #333390 had the
reference removed from its **title**, so the page rendered
`[REDACTED-CLOSING-REF]: Restore NODE_OPTIONS environment variable on Windows`.
The three declarations themselves are readable on the later page,
`reports/example-microsoft-vscode.html`, generated after this fix: *author's
text: "Fix #231076"*, *"This PR fixes #333395"*, *"Fixes #330410"*.

Five things changed, none of them the model or any prompt.

**The live path keeps the declaration; the evaluation still strips it.** A
live-only identity-only scrub, four lines. `harvest.scrub_patch` and the frozen
`CLOSING_RE` are untouched, so every published evaluation number is
byte-identical: 10/10, 15/15, 73.3% at 0.60 / 0.80 / 0.80, and the six-version
table.

**The declaration is quoted, not paraphrased.** The chip reads *author's text:
"Fix #231076", open issue, confirmed*. The first draft said *author says it
fixes #231076*, which is a claim about INTENT that a regular expression cannot
support: `This does not fix #123` matches the same pattern. Quoting the
author's own words, from the start of their own line, means a negation, an
unticked template checkbox and a `>` quote marker all reach the reader as
written, and the reader decides. `test_live_refs.py` locks all six cases.
References inside a fenced code block are skipped outright, one line in the
extractor. What survives is narrow and is stated on the page: a negated
reference to a genuinely open issue would still show a chip.

**A number outside our search window is no longer called invented.** The
investigator pulls the 300 most recent recorded problems; #231076 and #330410
sit below that window. The page said *claimed #231076, does not exist*, about a
real open issue, and the rework loop told the model the same thing and made it
retract a correct citation. Any number not in the window is now resolved once
against GitHub and reported as what it is: open, closed, actually a pull
request, genuinely absent, or **not checkable right now**. A 403 or a timeout
is never quietly downgraded to "invented". This reaches the verifier through a
membership object, with `agent_v4.py` unedited, so the evaluation path (which
builds its own plain set) cannot move.

**The line count was measured off a truncated string.** The patch is capped at
40000 characters before the counter runs (`live.py`), so every large submission
was undercounted. #333423 read **209 lines against GitHub's 608**, #333404 read
242 against 566. The control is exact, and it is scoped to a run rather than to
a commit: in that same run #333426's patch came in under the cap, and its count
of 473 matched GitHub's additions to the line. Both wrong ones were over it. The
count now comes from GitHub's own per-file `additions`, and the file fetch is
paginated, which it was not: above 100 changed files the file list was silently
short too.

One number needs saying out loud, because two committed files disagree about it
and neither is wrong. 473 and 544 are the same pull request read an hour apart,
with commits pushed to #333426 in between. `data/live-record-prefix.json` is the
pre-fix run of eight submissions, generated 2026-08-30 20:01 UTC, and records
473 lines for it; `reports/example-microsoft-vscode.html` is the later run of
nine, generated 21:00 UTC, and shows 544. Both name commit `e3ce07e8`, which is
microsoft/vscode's own default branch head: it pins the source the roles read,
not the state of any one submission, so it cannot separate the two figures. The
run is the unit of comparison here. The sha is not.

**A citation shape the model really returns used to crash the run.** `#333395
(memory tool)` starts with `#`, and `int(c[1:])` raises on it, after the entire
run has already been paid for. It now parses the same way the verifier always
did, `re.fullmatch(r"#(\d+)", c)`, and anything else is dropped rather than
counted as an invention.

**And the labels stopped claiming more than we checked.** Every chip now carries
one word saying where it came from: `fact` for anything you can re-derive from
GitHub with no model at all, `checked` for a reference the model proposed and we
then verified, `judgement` for the model's opinion with nothing behind it. The
group headings say "predicted merge" and "predicted not merged" rather than
"read these first" and "leave until last", because a bucket is a prediction
about a human decision and a reading order is a different claim.

**The gap this leaves, said plainly.** No automated check reads the live report.
`check_docs.py` parses offline replay metrics only, and teaching it to audit a
live page would be a new subsystem. The one thing `./run.sh eval` now checks is
that the committed example page is tracked at all. That gap is why the error in
the next section survived as long as it did.

## The sixth mislabelled number, and this one was about our own live run

Three sections up, this file said that inventing an accuracy figure for the live
tool "would be the sixth mislabelled number in this project". The sixth arrived
anyway, through a different door.

That section claimed **#333399 was correctly linked to reported problem
#333395**. The run record says the opposite. In
`data/live-record-prefix.json` that submission carries no citations, no
reported problems, pile 3, and a reason that explicitly REJECTS the link: *"No
verifiable evidence the linked issue #333395 or others actually correspond to
this bug"*.

Worth being precise about what went wrong, because it is not a typo. The line
describes a five-submission run at 145 seconds and 2.28 USD whose record this
repository does not have, and it contradicts the eight-submission record that is
now committed here as `data/live-record-prefix.json`. So it is not merely
contradicted, it is unreproducible, which is the worse of the two.

The cause is understood and is fixed in the section above: live mode was
redacting the author's declared reference before the model ever saw it, then
binning the submission for having no evidence of a link. Three of eight
submissions in that run declared a reference and all three were destroyed.

The corrected claim, taken from the record instead of from memory, specifically
the eight-submission run of 2026-08-30 20:01 UTC, taken **before** this change
and committed at `data/live-record-prefix.json`: of the eight open
submissions, **six returned at least one citation (an issue number or a file
path), and only one of those was an issue number**, two returned nothing, there
were zero invented references, and exactly one had a confirmed link to an
already-reported problem. The old bullet is **withdrawn**.

**Sixth time now**, and the first one caught by reading a shipped artifact
rather than a document. The other five are above. The common thread has never
been arithmetic; it is a sentence written once from a run that is gone.

## Size never ranked last, it ranked first

The section above titled "Deciding how much is worth reading today, and pointing
at one submission" says, verbatim: **"Size ranks last deliberately."** `README.md`
said the same thing. Both explained why: a large diff is work, not value, and
ranking by it would reward the exact thing this tool exists to filter.

`live.rank()` was sorting by `-lines`, biggest diff first. The code did the
opposite of both documents, and both documents had been describing an intention
rather than the behaviour. That sentence is **withdrawn**.

Size is removed from the ordering key rather than reversed. There is no honest
direction for it: small is not a virtue either. Tests went with it for a duller
reason, they are true of eight submissions out of eight, so that key was sorting
on noise. Both are still shown on the card.

The order is now a verified author-declared reference first, then a confirmed
link to an already-reported problem, then a confirmed description. When those
all tie, the newer submission goes first, and that is recency, not evidence: on
the eight-submission run, four of the eight cards have their position decided by
pull request number alone. Said plainly because this entry is about writing
claims from the record instead of from memory, and an "evidence ordering" that
sometimes sorts by nothing but recency is the kind of sentence that got us here.

## The investigator was searching a keyhole

Everything above tunes how the roles reason. This entry is about what they were allowed to see, which turned out to matter more.

`live.fetch_issue_corpus` pulled the 300 most recently filed problems and the investigator searched only those. On this repository that is about 300 numbers out of roughly 333,000. Anything reported more than a few days ago was unreachable, and no improvement to the model could have reached it. Two of the three declarations in the recorded run, #231076 and #330410, sat outside the window.

It now unions that local index with GitHub's own issue search.

**Reserved slots are the whole trick, and the obvious version does nothing.** The first design was "local first, then remote, cap the merged list at 8". Running the real matcher over the real corpus, local returns a full 8 hits on 9 of 9 submissions, because it keeps every document with any term overlap and truncates at 8. So the obvious merge would have let local crowd remote out completely and the change would have been a measured no-op. The merge alternates instead.

**The two search engines disagree about what a query means.** GitHub ANDs its terms; the local matcher soft-ORs them. The investigator writes one query, tuned for the soft-OR matcher, and we do not change its prompt. So a query like `memory leak extension host pseudoterminal` returns nothing from GitHub while `terminal memory leak` returns the plausible issue. On zero hits the search retries once with the three rarest words of the same query, scored by the idf table already built for the local index. No model call, no prompt change.

**What it actually bought, measured offline and free.** Over the 9 open submissions, 21 issues that the old corpus could not contain were surfaced, across 7 of the 9 cards. Five narrowing retries fired, no failures.

One is exactly the case this was built for. Submission #333418 is titled "migrate AsyncIterableObject to AsyncIterableProducer to fix memory leak", and an earlier run called it "a superficial class rename with no actual leak-fixing logic" and put it in the skip pile. Search surfaces #256854, "Review AsyncIterableObject usage: potential memory leaks and migration to AsyncIterableProducer", an open issue asking for precisely that migration. It is 76,000 numbers outside the old window.

**And some of it is noise, which is the honest half.** The same 21 include #519, "Allow to change the font size and font of the workbench". Raising candidate recall raises both signal and noise, and a wider net is not the same thing as a better answer.

**What we deliberately did not claim.** A before-and-after on the live queue would be worthless: the queue changes every day, four of the nine submissions turned over between two runs hours apart, and one card is eleven points of any rate computed over nine. So the retrieval measurement above is offline, deterministic, model-free, and repeatable; it is the only part attributable to this change. The end-to-end numbers from those two runs are not comparable and are not published as a trend.

**It is also invisible on the 15 closed cases, by construction.** `harvest.py` seeds the evaluation corpus with every declared target plus a band of distractors, so retrieval there is solvable by design. A retrieval improvement therefore cannot show up in the headline accuracy, and we are not going to pretend otherwise by quoting one.

## Three smaller things the same pass fixed

**The claim checker was reading an arbitrary file.** It took the first source file GitHub happened to list, which on a 24-file submission is usually a config or barrel file that says nothing about the claim. It now reads the file that gained the most lines. This sits behind a default argument: the 15 evaluation cases carry no per-file counts, so they take the original branch and the scored path is unchanged by construction rather than by hope.

**It was also reading the wrong repository.** `fetch_source` requested `repos/microsoft/vscode/contents/` no matter which repository the tool was pointed at, so `./run.sh live some/other-repo` read VS Code's source and still returned a verdict on it. It takes the repository now, defaulting to VS Code so the evaluation is untouched.

**"Has tests" was true on every card of every run.** The path pattern matches any test directory and this repository has them everywhere, so the chip never varied and carried no information. It now reports added test lines, which ranges from 3 to 550 across the same nine submissions. #333418 touches three test files and adds three lines, which the old chip flattered as "has tests".

## A regression check that could not regress

`./run.sh agent` returning 73.3% was cited as proof that the two changes above were safe. It was not proof of anything. The published numbers replay from committed JSON and never enter `check_claims` or `fetch_source`, so those two functions had no test coverage at all and the headline number was structurally incapable of moving.

Twelve offline checks now call them directly: the file chooser's fallback, its tie-breaking, the repository defaulting, the cache key, the merge's reserved slots, deduplication across the two sources, the counted search failure, and the filter that stops a pull request being offered as a reported problem. Each was verified by breaking the code and confirming the check fails. One of them was written vacuous on the first attempt, asserting something that could not fail, and was replaced.

## The tool had no idea it had ever seen your queue before

A maintainer does not triage once. They open the queue on Monday, again on Wednesday, again on Friday, and most of what they see is what they already saw. Every run until now started from nothing, so the third visit re-presented the same twenty submissions with the same conclusions and no indication which of them were actually new. That is the original problem wearing a different hat.

`memory.py` is a plain JSON file per repository. It carries three things forward and refuses to carry anything else.

**What is new since your last visit.** On a repeat run the page marks genuinely new submissions and tells you which visit this is for the rest. Simulated over the nine live submissions plus one new arrival: visit one flags 9 of 9 as new, visit two flags exactly 1. That is the difference between reading ten cards and reading one.

**How long something has been waiting, and whether we already put it in front of you.** A submission the tool ranked into your reading list three visits ago that is still open is a different object from one filed this morning, and the page now says so.

**Resolved issue lookups.** Whether #231076 exists and is open is a fact about the repository, not about this run. Re-asking GitHub for it every time is a wasted call, and calls are what cost money and hit rate limits. Recalled lookups are reported to stderr so the saving is visible rather than assumed.

**What it deliberately does not remember, which is the more interesting half.** No model output. Buckets, reasons and claim verdicts are re-derived every single run. Caching a judgement would let a stale conclusion silently outlive the evidence that produced it, and this file already contains six entries about claims that outlived their evidence. A cached fact is a saving. A cached judgement is a lie waiting to happen.

Two failure modes are handled explicitly because a memory that can break the tool is worse than no memory. A corrupt or unreadable store degrades to no-memory rather than raising, and an unwritable store prints a warning and lets the run finish. Both are tested. So is the rule that `unresolved`, meaning we could not reach GitHub, is never cached: one rate-limited run must not poison every later run with a fact we never actually learned.

Six offline checks cover it, including the corruption and unwritable paths.

## A script is a thing you remember to run

Every command in this project assumes the maintainer opens a terminal, remembers the incantation and reads a page. That is a fine way to demonstrate a system and a poor way to fit into someone's Tuesday. The assistant they already have open is where the question actually gets asked.

`mcp_server.py` exposes the same triage over the Model Context Protocol, so "what should I look at in vscode today" is answered where the maintainer is standing.

**The browser page stays, and the reason is a real constraint rather than a preference.** Chat is bad at tables. Nine submissions with five evidence chips, a rank and a reason each is a grid, and a grid pasted into a conversation is unreadable. So every tool returns a short summary inline and writes the full page beside it, handing back the path. Summary where you are, detail where detail belongs.

**The free tool is the important one.** `whats_new` reads only the memory store: no model call, no network, no cost. It answers "is there anything worth paying for today", and on a quiet day that is the entire interaction. Putting the cheap question first is the design; a tool that can only answer expensively will get run less often than it should.

**We did not add the SDK, and that was the interesting decision.** The reproduction promise is a clean clone plus the standard library plus `gh`, with no install step. An MCP SDK would have been this project's first dependency, spent on one feature, and every judge running from a fresh clone would have hit an install wall. The stdio transport is newline-delimited JSON-RPC 2.0, which is a loop over stdin, so we wrote the loop. About 150 lines against the cost of the project's "no install" claim.

**Nothing it exposes can act.** The tools read, and they write one HTML file. No merge, no close, no comment, no label, and every summary says so in its final line.

Seven checks drive the server over its real transport with no network and no model, including the two failures that would be invisible in a demo and fatal in use: replying to a notification, which corrupts the stream, and a raising tool killing the transport instead of returning readable error content. Registration could not be exercised on the build machine, where local policy blocks adding MCP servers, so the protocol is tested directly, which is the stronger evidence anyway.

## The MCP server shipped broken, with seven passing tests over it

Worth its own entry because the bug is boring and the reason it survived is not.

`stdout` is the protocol. MCP over stdio is newline-delimited JSON-RPC on standard output, and `live.run()` prints its progress with plain `print()`, which also goes to standard output. So every progress line was injected into the protocol stream as raw text:

```
{"jsonrpc": "2.0", "id": 1, "result": {...}}
[live] fetching pull request #333390 from microsoft/vscode
[live] 300 recorded problems
```

The first triage call from any real client would have corrupted the session. The server was committed with seven passing checks over it, and not one could see this, because every one of them exercised a handler that never reaches `live.run()`. The tests covered the protocol surface. The bug was underneath it.

**Then the regression test for it was also written unable to fail.** The first version passed a fresh `StringIO` to `serve()`, so the tool's `print()` and the protocol writer never shared a stream, which is exactly the condition that produces the bug. It passed with the fix removed. It only means anything when both are bound to one stream the way the real server runs, and it is now verified by deleting the fix and confirming a `JSONDecodeError`.

That is three tests in this project written so they could not fail, all with the same shape: **asserting on a channel the failure cannot reach**. The vacuous test in the union-search set was the same mistake, and so was citing `./run.sh agent` as proof that a change to `check_claims` was safe when the replay path never calls it.

**The lesson, and it is the one we would carry to the next agent we build.** A test you have not seen fail is a decoration. Every check added since is verified by breaking the code first and watching the assertion fire, and the ones that could not be made to fail were deleted rather than kept for the count. The specific trap for agent work is that the seam you mock is usually the seam the bug lives in: mock the model and you stop testing the plumbing, hand the server a private stream and you stop testing the transport. Writing the harness is not the same as writing a test, and passing is not the same as working.


## Which pile is a useless answer when there is only one submission

Everything in this project sorts a queue. Pointed at a single pull request that framing collapses: a maintainer looking at one change does not want to know which of three piles it falls in, they want to know whether it is any good and what to ask for before merging.

So on a single submission the tool now also reviews the work. Overall quality, what it genuinely does well, what should be improved with a file and a reason attached to each, anything that should block a merge outright, and what breaks if the judgement is wrong.

**It is kept blind to our own conclusion, and that is the design.** The reviewer gets the diff, the source at a pinned commit and the line counts. It never sees the bucket, the evidence chips or what the investigator found. Handing a reviewer the answer we already reached invites it to agree with us, and a reviewer that agrees with the thing it is checking is worth nothing. It is rendered in its own block on the page, visually separate from the chips, because the chips are checked facts and this is a judgement, and running them together would let a judgement borrow the credibility of a fact.

On `microsoft/vscode#333418`, a rename titled as a memory-leak fix, it returned `workable` and found something nobody asked it to look for: a hand-edit to a pipeline config file whose own header forbids editing it by hand. It also named the real tension, that the title promises a leak fix while the visible diff is a pure rename, so a maintainer merging it takes on a false narrative. 0.55 USD.

Review is ON by default for one submission and OFF for a queue scan, because it is a per-submission model call and a scan should not pay for it on every card.

## Scanning the whole queue, and what that actually costs

The scan-all flag does what it says: every open submission, not the most recent handful. The page cap that bounded a normal fetch lifts with the limit, so "all" does not quietly mean "the first 250".

The number that came back is the point. **microsoft/vscode has 1,782 open non-draft pull requests.** (GitHub's own counter says 2,442, which includes 660 drafts; the tool skips drafts, so 1,782 is the number it would actually read.) A full scan is roughly 800 USD and twelve hours. So both the flag and the MCP tool refuse and quote the bill first, and only proceed once it is confirmed.

That figure retroactively justifies two features we could not demonstrate on a nine-item queue. The today-caps of 5 and 8 never fired in any test run and looked like dead weight; at 1,782 they are the difference between a reading list and the original problem. And memory stops being a nicety: the gap between re-reading 1,782 cards and reading the handful that are new is the entire product.

## The server could not start

The MCP config used a relative path, so it only launched if the client happened to start in this directory, and every path in the project has the same dependency: the evaluation cache, the reports directory, the memory store. Started from anywhere else it either failed to launch or launched and could not find its own data.

`mcp_server.py` now anchors to its own file rather than to the caller, and a new install target writes the absolute path for whatever clone you happen to have, which is the part a judge needs.


## A number is not a choice until it has a price on it

The queue depth started at 8, which was a demo rather than a default, and briefly became a silent 100. A silent 100 is about 45 USD and forty minutes, and this is a public repository: someone clones it, types the obvious command, and finds out the price afterwards. That is a bad way to meet a tool.

So the depth is now chosen, not assumed. The default target is the 100 most recent open submissions, and anything past a dozen stops and offers the options with the bill attached to each:

```
      5   about   2.25 USD,   2 min   a quick look, enough to see the shape of the queue
     25   about  11.25 USD,  10 min   a morning's reading
    100   about  45.00 USD,  42 min   the default depth
   1782   about 801.90 USD, 743 min   every open submission
```

**"100" means nothing to someone who has not priced a run.** That is the whole point of putting the cost on every line: it turns an invisible decision into a visible one. An option larger than the repository itself is never offered, so a small project is not asked whether it wants 100 of its 7 submissions.

The options are returned as data rather than baked into a message, because two surfaces need the same choice. In a terminal the tool asks directly. An MCP tool cannot ask anything, so it hands the assistant the priced options and lets the assistant put them in front of the maintainer, then takes the answer back as `limit` plus `confirm_cost`.

With no terminal and no confirmation, it prints the menu and spends nothing, so a script or a CI job can never discover the price after the fact.


## The first command a judge runs crashed on their machine and passed on ours

`./run.sh eval` read its fixture from `reports/microsoft-vscode.json`. That directory is gitignored, so the file exists only on a machine that has already paid for a live run. On a fresh clone the whole target died with `FileNotFoundError`, and because `run.sh` uses `set -euo pipefail`, everything after it went down too: the twenty protocol checks, the documentation guard and the reference baseline. The suite passed here for the worst possible reason, which is that we were not the audience.

The fixture now comes from `data/live-record-prefix.json`, which is tracked. Verified the way it should have been from the start: copy only the tracked files into an empty directory, no `.git`, no artifacts, and run the command a judge would run. Exit 0, twenty of twenty.

Three more things the same review found, all of the same family, a claim that was true only where it was written.

**The committed MCP config named one machine.** `mcp-install` wrote an absolute path into `.mcp.json` and that got committed, so the file worked on exactly one computer and published a home directory into a public repository. It is back to the relative form, which is what `cd PR-slop && claude` needs, and the installer stays as the local override.

**The isolation probe pointed at a path that only exists here.** It proves the model cannot read the answer key by asking it to open the answer key. The path was hardcoded absolute, so on anybody else's clone the negative control asked for a file that does not exist. It failed closed rather than open, so no published number is wrong, but the proof was only a proof on one machine. Resolved at run time now.

**Three output modes were two.** `inline` appended the report path exactly like `both`, so they were byte-identical, and the check covering it asserted on a string every branch produced. Fourth unfalsifiable test in this project. The modes are now distinct and the check compares all three against each other. The redundant whitelist behind it was deleted rather than kept: `_shape` already fell through correctly, so the guard was unreachable and the test could not tell the difference.

Two numbers were also wrong in the safe direction and are now right. The 1,782 figure is non-draft submissions; GitHub's own counter says 2,442 because it includes 660 drafts, which this tool skips. And the time estimate used 25 seconds per submission against our own recorded 29, running about 16% optimistic.
