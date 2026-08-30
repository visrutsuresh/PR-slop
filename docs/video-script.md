# Video script, five minutes

Everything on screen is real and in this repository. Timings are a guide.

---

## 0:00 to 0:40 — the problem, and why I am the one telling you

Volunteers maintain free software. They are buried in machine-written submissions. The curl project says it is "effectively being DDoSed" by them. Roughly one in five of its submissions last year were slop. OCaml maintainers rejected a single AI-written pull request of thirteen thousand lines.

But the interesting question is why the slop exists.

**On screen: two real job adverts.**

- Chubb, desirable: *"Contribution to open-source AI projects"*
- Singtel: *"Public portfolio, hackathon wins, open-source contributions"*

I collected both during my own internship search. Employers ask for open source contributions. People who need that line produce volume, and machines make volume free. Nobody is being malicious.

I am not a maintainer. I am the person standing under that pressure. That is why I picked this.

---

## 0:40 to 1:10 — the baseline, and its score

**On screen: `./run.sh baseline`**

One prompt per submission, no tools. This is the comparison micro1's own brief suggests. I used it rather than something weaker on purpose.

**33.3%.** The floor for three piles is 33.3%. It does exactly as well as guessing.

---

## 1:10 to 2:20 — one real run, end to end

**On screen: `./run.sh agent`, then open one trace in `traces/`.**

Four roles, and a loop.

The **investigator** decides what to search for. Watch this: from a title that says none of these words, it wrote `snippet tab stop limit 10 nested placeholders`. It is using the words a person *reporting* a problem would use, not the words a developer *fixing* it uses. It found the right one. It can also search again if the first attempt was poor, and it chose to do that six times across fifteen cases.

The **claim checker** then reads the real source at a pinned commit and tests whether the code does what the description says.

The **adjudicator** decides the pile. The **verifier** checks every claim and can send the work back.

Then the product itself: **`./run.sh triage`**. One page. What to read first and why, the normal queue, what to leave. Every number on it resolves against the repository. Nothing is posted, closed or merged. A human decides.

---

## 2:20 to 3:10 — six versions, including two I broke myself

**On screen: the version table.**

The first agent scored **46.7%**, far worse than a simple script. Its claim checker said "the code does not match the description" on three submissions, and the decider binned all three. All three had actually been merged.

It had confused *"I do not rate this code"* with *"this was not accepted"*.

Version 3 fixed that and reached 73.3. Version 4 fixed two handover faults between the agents, and this is the part I would tell another builder: **every worker behaved sensibly on its own. The system still got it wrong because information was lost between them.** The searcher's answer arrived at the decider as a bare number with no explanation, so the decider ignored it.

Version 5 was mine. I made the searcher's verdict binding, having loosened it the version before. Loose plus binding means everything lands in one pile. **73.3 down to 46.7.**

I stopped at six, because one case is worth 6.7 points on fifteen cases, and past that I am fitting noise, not improving anything.

---

## 3:10 to 4:00 — the flaw in the whole idea, and what I did about it

Here is the uncomfortable part.

Every version predicts what a maintainer *did*. So if a maintainer overlooks something good and closes it, and my tool correctly says the work is good, **I mark my own tool wrong.** The scoring fights the product.

**On screen: pr-308696.** The one case no version out of six ever got right. Real code. Fixes a genuinely reported problem. Confirmed against the actual source. Closed anyway. Six versions all said "this is good work" and I scored all six as mistakes.

So I added a second output that judges the work rather than the decision: does it name a genuinely reported problem, does it carry tests, does the code match its description. All facts, no human verdict. Sixteen factual claims, sixteen hold up.

**On screen: the SECOND OPINION section of the triage page.**

And now the failure becomes the feature. That section lists well-supported work that was closed anyway. pr-308696 is the top line. That is not my tool being wrong. **That is my tool finding something a human may have missed**, which is the thing a maintainer would most want.

---

## 4:00 to 4:35 — what I removed, and three numbers I made up

**Removed:** the fully agentic version scored 46.7 against 73.3 and cost three and a half times as much. It is still in the repo, runnable, with its saved answers, so the negative result reproduces.

**And three times today I published a number with no basis, and caught each one.** A citation score of 86.7% that was really twelve file paths copied out of the question. An evidence figure of 61.5% that counted "made no claim" as "lied". And "roughly 31 minutes of reading" from a formula I invented on the spot, in a project that had *already* dropped a made-up time metric an hour earlier.

All three are in the changelog. Writing a rule against it after the first one did not stop the second or the third. What caught them was a number sitting oddly next to another number.

---

## 4:35 to 5:00 — the hot take

"Closed without merging" looks like it should mean "rejected as bad". On vscode it mostly does not. Of seventeen I inspected: four were bots, about ten were maintainers closing their own real work in favour of another approach, and **exactly one** looked like slop.

So any triage tool built on the metadata a project records for free is measuring maintainer **behaviour**, not maintainer **judgment of quality**. That is enough to build something genuinely useful. It is not the same claim as "this detects AI slop", and I would rather say so than let a good-looking number imply it.

---

## Shot list

| Time | On screen |
| --- | --- |
| 0:00 | the two job adverts |
| 0:40 | `./run.sh baseline`, the 33.3% |
| 1:10 | `./run.sh agent`, then a `traces/agent-*.md` file |
| 1:50 | `./run.sh triage`, the page |
| 2:20 | the six-version table |
| 3:10 | pr-308696 in `data/cases/`, then SECOND OPINION |
| 4:00 | `CHANGELOG.md`, the three made-up numbers |
| 4:35 | the 17-case breakdown |
