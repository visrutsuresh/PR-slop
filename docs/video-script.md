# Video script, five minutes

Written to be read aloud. Every command in the shot list has been run and produces what the script says it produces. Timings are the target, not a stopwatch.

Two rules while recording. Say the number that is on the screen, not the number in your memory. And when something is a guess, call it a guess in the same breath.

---

## Before you hit record

**Window width.** Record at 1440 or wider. The board misaligns slightly between 1120 and 1280 pixels. Fixed in the generator, but wider is safer and the board has room to breathe.

**Register the MCP server.** One command, from inside the repo:

```
claude mcp add pr-slop -- python3 $(pwd)/src/mcp_server.py
```

Confirm it took before you record. `claude mcp list` should show `pr-slop`.

**What costs money on camera.** `whats_new` is free, offline, instant. `triage_pull_request` is about 0.55 USD for one submission. `triage_queue` on a large repo runs into real money and asks before spending. The script only has you run the first two. Do not run `triage_queue` on vscode's full queue while recording; 1,782 open pull requests is roughly 800 USD.

**Have these open:** a terminal in the repo, your assistant with the MCP server registered, and `reports/example-microsoft-vscode.html` in a browser tab.

---

## 0:00 to 0:30, the problem

**Shot: you on camera, or a slide with two job adverts.**

> Every maintainer I read says a version of the same thing. The pull requests keep coming, more of them than ever, and a growing share are written by a model. Some are real work. Some are a plausible-looking diff with a confident description attached. Both look identical in a list of forty.
>
> The expensive part is not merging. It is deciding what to open first.

Point at the phrase "open-source contributions" in both adverts.

> This is PR-slop. You point it at a repository, and it hands back your reading order.

---

## 0:30 to 1:00, the floor

**Shot: terminal.** Type:

```
./run.sh baseline
```

> Before anything clever, here is the honest floor. One prompt, the whole pull request, asked to sort it into three piles.

Point at `balanced accuracy : 33.3%`.

> Three piles. Guessing scores 33.3. This scores 33.3. It is not slightly better than a coin toss, it is exactly a coin toss, and it took a model to achieve it.

---

## 1:00 to 2:20, the launch demo, using it for real

**This is the centre of the video. Record your screen with the assistant open.**

You are not running a script. You are talking to your own assistant, and the tool is just there.

**Beat one, free.** Type into the assistant:

> what's new on microsoft/vscode

Let the answer land on screen. It will say something close to: three previous visits, last on 2026-08-30, two submissions tracked, and that `#333390` has now been sitting in your reading list across two visits.

> That cost nothing. No model call, no network. It read what it remembered from last time. If nothing is new, there is nothing to pay for, so this is the first question rather than the last.

**Beat two, one real submission.** Type:

> triage pull request 333418 on microsoft/vscode, and review the code

Say this while it runs:

> Now it is doing real work. It reads the pull request, writes its own search against the project's own issue tracker, opens the actual source at a pinned commit to check whether the code does what the description claims, and then a separate role argues with the result before anything is shown to me.

When the answer comes back, point at two things.

> The summary is here in the chat, because that is where I am. And it also wrote a page, because chat is a bad place for a table.

**Beat three, the page.** Open the file it names.

> Three columns. That is my reading order. Read first, read next, likely to be closed.
>
> This one, `#333418`, is the one worth showing you.

Click into it.

> Everything here is sorted by how much you should trust it. **Fact** is re-derivable without a model at all: lines changed, test lines added. **Checked** means the model made a claim and we went and verified it against GitHub. **Judgement** is the model's opinion with nothing behind it.
>
> And on this one the judgement says the code does not match its own description. That is the most useful thing the tool produces, so it is the loudest mark on the card, not a footnote.

Scroll to the citations block.

> These are the source files it actually opened, at this exact commit, to check that claim. Click through and you land on the line it read. The tool is not asking you to trust it. It is showing its work.

---

## 2:20 to 3:00, six versions, two of which I broke

**Shot: terminal.** Type:

```
./run.sh versions
```

> Six versions, recomputed from committed answers every time this runs, so the table is checkable rather than claimed.

Point at v1, then v5.

> Version one was the fully agentic build, and it was worse than the script I already had. Version five was a change that sounded obviously right when I made it and cost twenty-seven points.
>
> Both are still in the repository. I did not delete the versions that made me look bad, because the changelog is the deliverable and a changelog with only wins in it is marketing.

---

## 3:00 to 3:50, the flaw I built in on purpose

**Shot: terminal.** Type:

```
./run.sh triage 308696
```

> Here is the problem with the whole evaluation, and I want to say it before a judge finds it.
>
> The right answer, the thing I score against, is what a maintainer actually did. Merged, or closed. So a tool that correctly spots something valuable a maintainer overlooked gets marked wrong for being right.

Point at the second-opinion note.

> This one is real code, it fixes a genuinely reported problem, I confirmed it against the source. It was closed anyway. Six versions of this system, and not one of them ever got it "right", because being right here means predicting a human.

Then:

```
./run.sh evidence
```

> So there is a second output that ignores the human decision entirely and only asks whether the work is any good.

Point at `15 factual claims, 15 hold up`.

> Fifteen factual claims, fifteen hold up. That is the number I would actually defend.

---

## 3:50 to 4:30, what I removed, and three numbers I invented

**Shot: `IMPROVEMENT-CHANGELOG.md`, search for "made-up".**

> The experiment I removed is in here with the twenty-seven points it cost.
>
> And so are three figures I published that turned out to be invented. Not wrong. Invented. I wrote numbers that no run produced, and I only found them because something went back and re-derived every claim from the artifact.

Optionally, and this is the strongest thing you can say:

> That happened again while I was finishing this. Twelve claims across this repository turned out to be true only in the file that made them. Four of those twelve were introduced by the fix for one of the others. Not one was caught by a test.
>
> Which is the entire thesis of this project, happening to this project.

---

## 4:30 to 5:00, the hot take

**Shot: you on camera.**

> The hot take is this. The slop problem is not a writing problem, and you cannot fix it with a better detector.
>
> I looked at seventeen closed submissions on vscode by hand. Four were bots. Ten were insiders. Exactly one looked like slop. The flood everyone is bracing for is mostly not here yet, and the real cost today is not bad pull requests, it is that good and bad ones are indistinguishable until somebody reads them.
>
> So this does not judge writing. It never scores style. It checks three things you can verify: does it name a problem that is really in your tracker, does the source at a pinned commit match the description, and how much code and test code is there.
>
> It never acts. It never closes anything, never comments, never merges. It hands you an order to read in, and shows you the evidence for it.
>
> That is the whole product.

---

## Shot list, every row is something you can literally type

Nothing below needs an account or a network except the two MCP beats.

| Time | Shot | Type this | Point at |
| --- | --- | --- | --- |
| 0:00 | you, or a slide | (two job adverts) | "open-source contributions" in both |
| 0:30 | terminal | `./run.sh baseline` | `balanced accuracy : 33.3%` |
| 1:00 | **assistant, screen record** | `what's new on microsoft/vscode` | 3 previous visits, `#333390` seen twice, "no cost" |
| 1:20 | **assistant, screen record** | `triage pull request 333418 on microsoft/vscode, and review the code` | the summary inline, and the page path it writes |
| 1:50 | **browser** | open the page it named | three columns, then click `#333418` |
| 2:05 | browser | scroll the detail page | the three evidence tiers, then the citations block |
| 2:20 | terminal | `./run.sh versions` | v1 worse than the script, v5 down 27 points |
| 3:00 | terminal | `./run.sh triage 308696` | `NOTE: closed without merging, but the evidence above is strong` |
| 3:30 | terminal | `./run.sh evidence` | `15 factual claims, 15 hold up` |
| 3:50 | editor | `IMPROVEMENT-CHANGELOG.md`, search "made-up" | the three invented figures |
| 4:30 | you | (nothing) | the hot take |

**If a beat runs long, cut 3:50.** The changelog section is the one a judge will read anyway. Do not cut the MCP demo or the evidence tiers.

**One rehearsal note.** `./run.sh versions` prints more than a screen. Scroll slowly or pre-size the window. The numbers are the point and an unreadable frame wastes the shot.

**If you have thirty spare seconds**, run `./run.sh probe` on camera. It proves the model cannot read the answer key, and it is the single most convincing thing here for anyone who suspects the evaluation is rigged.

---

## The question to be ready for, and the answer

A judge who knows the literature may raise Liang et al. 2023, which found seven AI-text detectors flagged over half of 91 TOEFL essays by non-native English writers as machine-written, one of them at nearly 98 percent. A tool for spotting machine-written pull requests invites exactly that objection. Have this ready:

> This is not a text detector. It never scores writing style. It scores three checkable things: does the pull request name a problem that is actually in the issue tracker, does the source at a pinned commit match what the description says it does, and how much code and test code is there. Author identity is stripped before the model sees anything. The Liang failure mode is stylometry punishing people who write English differently, and there is no stylometry here. The honest residual risk: the adjudicator is a language model reading the pull request body, so prose style can leak in indirectly, and I have no test for that.

The last sentence is what makes it credible. Do not drop it.

---

## Two things not to overclaim on camera

**"It writes its own search."** True, and scoped to the title: the words it searched for are not in the title. Some of them do appear further down in the body, which is on screen. Say "from a title with none of these words" and it is exactly true. Do not stretch it to "words that appear nowhere".

**The fifteen cases.** If a judge raises the sample size, agree first. The repository already says the headline is a tie, that one case moves the number 6.7 points, and that the pre-registered target is unfalsifiable at this n. Saying it before they do is worth more than defending it after.
