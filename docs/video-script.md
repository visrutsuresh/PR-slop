# Video script, five minutes, voiceover edition

Built for an AI voiceover. Each section has two blocks.

**SCREEN** is what you capture. No talking, just the recording.
**VOICEOVER** is pure prose, ready to paste into the voice tool with nothing to strip out. Numbers are spelled the way they should be spoken, so the voice does not read "hashtag three three three four one eight".

Total voiceover is 750 words. At 150 words per minute that is 300 seconds, and most AI voices run faster than that, so you have room but not much. Word counts are given per section so you can trim if your voice runs fast or slow.

Record the screen first, then lay the voice over it. The screen actions are slower than the narration in most sections, which is correct: let a command finish before the next line starts.

---

## Before you record

**Window width.** 1440 pixels or wider. The board misaligns slightly between 1120 and 1280.

**MCP server.** It must be registered before you record. If `claude mcp add` is refused by policy, the fix is in `docs/` and needs a `sudo` copy you run yourself. Confirm with `claude mcp list` and make sure `pr-slop` appears.

**What costs money.** `whats_new` is free, offline, instant. `triage_pull_request` is about fifty five cents for one submission. **Do not run `triage_queue` on the vscode queue while recording.** It holds 1,782 open pull requests, roughly 800 dollars.

**Have ready:** a terminal in the repo, your assistant with the server registered, and a browser tab.

---

# Section 1, zero to thirty seconds

### SCREEN

Either you on camera, or a still slide showing two job adverts with the phrase "open-source contributions" visible in both. Hold it for the full thirty seconds. No motion needed.

### VOICEOVER (66 words)

```
Every maintainer says a version of the same thing. The pull requests keep coming, more than ever, and a growing share are written by a model. Some are real work. Some are a plausible looking diff with a confident description attached. Both look identical in a list of forty. The expensive part is not merging. It is deciding what to open first. This is PR slop.
```

---

# Section 2, thirty seconds to one minute

### SCREEN

Terminal, full screen. Type and run:

```
./run.sh baseline
```

Let it finish. Leave the final block on screen for at least five seconds. The line that matters is `balanced accuracy : 33.3%`.

### VOICEOVER (67 words)

```
Before anything clever, here is the honest floor. One prompt, the whole pull request, asked to sort it into three piles. Thirty three point three percent. There are three piles, so guessing scores thirty three point three. This scores thirty three point three. It is not slightly better than a coin toss. It is exactly a coin toss, and it took a language model to achieve it.
```

---

# Section 3, one minute to two minutes twenty. The demo.

This is the centre of the video. Three screen recordings, one continuous voiceover.

### SCREEN 3A, about twenty seconds

Your assistant, screen recorded. Type and send:

```
what's new on microsoft/vscode
```

The answer is instant and free. It will report three previous visits, two submissions tracked, and that pull request 333390 has stayed in your reading list across two visits. Hold on the answer.

### SCREEN 3B, about thirty seconds

Same window. Type and send:

```
triage pull request 333418 on microsoft/vscode, and review the code
```

This one costs about fifty five cents and takes a moment. Record the wait, you can speed it up in the edit. When it returns, hold on two things: the summary in the chat, and the file path it says it wrote.

### SCREEN 3C, about thirty seconds

Open that file in the browser. Show the three columns. Click into pull request 333418. Scroll slowly down the detail page, pausing on the three evidence blocks, then on the citations block near the bottom.

### VOICEOVER (186 words)

```
Here it is in the tool I already use. First question, what changed since last time. That was free. No model call, no network. It read what it remembered. If nothing is new, there is nothing to pay for, so it is the first question rather than the last.
Now one real submission. It reads the pull request, writes its own search against the project's issue tracker, opens the source at a pinned commit to check whether the code does what the description claims, and a separate reviewer argues with the result before I see it.
The summary comes back in the chat. It also writes a page, because chat is a bad place for a table.
Three columns. That is my reading order.
Everything is sorted by how much you should trust it. Fact is re-derivable without a model. Checked means the model made a claim and we verified it. Judgement is opinion with nothing behind it.
And these are the files it actually opened, at this commit, to check that claim. It is not asking you to trust it. It is showing its work.
```

---

# Section 4, two twenty to three minutes

### SCREEN

Terminal. Type and run:

```
./run.sh versions
```

The table is longer than one screen. Pre-size the window or scroll slowly. Rest on the row for version one, then on version five. Both numbers need to be readable in the frame.

### VOICEOVER (88 words)

```
Six versions, recomputed from committed answers every time this runs, so the table is checkable rather than claimed. Version one was the fully agentic build, and it was worse than the plain script I already had. Version five was a change that sounded obviously right when I made it, and it cost twenty seven points. Both are still in the repository. I did not delete the versions that made me look bad, because the changelog is the deliverable, and a changelog with only wins in it is marketing.
```

---

# Section 5, three minutes to three fifty

### SCREEN 5A, about twenty five seconds

Terminal. Run:

```
./run.sh triage 308696
```

Rest on the note at the end, the one saying it was closed without merging but the evidence is strong.

### SCREEN 5B, about twenty five seconds

Same terminal. Run:

```
./run.sh evidence
```

Rest on the line reading `15 factual claims, 15 hold up`.

### VOICEOVER (121 words)

```
Now the flaw in the whole idea, and I want to say it before a judge finds it. The answer I score against is what a maintainer actually did. Merged, or closed. So a tool that correctly spots value a maintainer overlooked gets marked wrong for being right.
This one is real code. It fixes a genuinely reported problem. I confirmed it against the source. It was closed anyway. Not one of six versions ever got it right, because being right here means predicting a human.
So there is a second output that ignores the human decision entirely, and only asks whether the work is any good. Fifteen factual claims, fifteen hold up. That is the number I would actually defend.
```

---

# Section 6, three fifty to four thirty

### SCREEN

Editor showing `IMPROVEMENT-CHANGELOG.md`. Search for the word "made-up" and let the match highlight on screen. Scroll slowly through that entry. Do not stop on any one line for long, the point is the volume of it.

### VOICEOVER (98 words)

```
The experiment I removed is in here, with the twenty seven points it cost. So are three figures I published that turned out to be invented. Not wrong. Invented. I wrote numbers no run ever produced, and I only found them because something went back and re-derived every claim from the artifact.
That happened again while I was finishing this. Twelve claims across this repository turned out to be true only in the file that made them. Four of those twelve were introduced by the fix for one of the others. Not one was caught by a test.
```

---

# Section 7, four thirty to five minutes

### SCREEN

You on camera. If you would rather not be on camera, a plain slide with the three checks listed works: names a real problem, source matches the description, how much code and test code.

### VOICEOVER (124 words)

```
The hot take is this. The slop problem is not a writing problem, and you cannot fix it with a better detector.
I read seventeen closed submissions by hand. Four were bots. Ten were insiders. Exactly one looked like slop. The flood everyone is bracing for is mostly not here yet. The real cost today is that good and bad are indistinguishable until somebody reads them.
So this never scores style. It checks three things you can verify. Does it name a problem that is really in your tracker. Does the source at a pinned commit match the description. And how much code and test code is there.
It never acts. It hands you an order to read in, and shows you the evidence.
```

---

# Capture checklist

Record these in any order, then assemble. Screen only, no audio needed.

| # | Duration | What to capture |
| --- | --- | --- |
| 1 | 0:30 | Slide, two job adverts, or you on camera |
| 2 | 0:30 | Terminal, `./run.sh baseline`, rest on the accuracy line |
| 3A | 0:20 | Assistant, `what's new on microsoft/vscode`, rest on the answer |
| 3B | 0:30 | Assistant, `triage pull request 333418 on microsoft/vscode, and review the code` |
| 3C | 0:30 | Browser, the page it wrote, three columns, click 333418, scroll to citations |
| 4 | 0:40 | Terminal, `./run.sh versions`, rest on version one and version five |
| 5A | 0:25 | Terminal, `./run.sh triage 308696`, rest on the closing note |
| 5B | 0:25 | Terminal, `./run.sh evidence`, rest on fifteen of fifteen |
| 6 | 0:40 | Editor, changelog, search "made-up", scroll |
| 7 | 0:30 | You on camera, or the three-checks slide |

**Optional, thirty seconds if you have room:** terminal, `./run.sh probe`. It proves the model cannot read the answer key, and it is the most convincing thing here for anyone who suspects the evaluation is rigged. If you use it, add this line to section 6's voiceover: "And this proves the model never had access to the answers, because I expected somebody to ask."

**If you run long, cut section 6.** A judge reads the changelog anyway. Do not cut section 3 or the evidence tiers in 3C.

---

# Voiceover settings

Read the blocks in order, one file per section, so you can retime without re-rendering everything.

Numbers are already spelled for speech. Do not paste the shell commands into the voice tool, they are screen actions only.

If your voice tool supports pace, slow it slightly for section 3, which carries the most new information, and for the last two sentences of section 7.

---

# The question to be ready for

Not part of the recording. Have it ready if a judge asks live.

A judge who knows the literature may raise Liang and colleagues, 2023, which found seven AI-text detectors flagged over half of ninety one essays by non-native English writers as machine-written, one of them at nearly ninety eight percent. A tool for spotting machine-written pull requests invites that objection.

> This is not a text detector. It never scores writing style. It scores three checkable things: does the pull request name a problem that is actually in the issue tracker, does the source at a pinned commit match what the description says it does, and how much code and test code is there. Author identity is stripped before the model sees anything. The Liang failure mode is stylometry punishing people who write English differently, and there is no stylometry here. The honest residual risk: the adjudicator is a language model reading the pull request body, so prose style can leak in indirectly, and I have no test for that.

The last sentence is what makes it credible. Do not drop it.

---

# Two things not to overclaim

**"It writes its own search."** True, and scoped to the title. The words it searched for are not in the title. Some do appear further down in the body, which is on screen. The voiceover in section 3 already avoids this by not making the claim at all. If you ad-lib it, say "from a title with none of these words".

**The fifteen cases.** If a judge raises the sample size, agree first. The repository already says the headline is a tie, that one case moves the number six point seven points, and that the pre-registered target is unfalsifiable at this sample size. Saying it before they do is worth more than defending it after.
