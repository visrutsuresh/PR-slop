# Video script, five minutes, voiceover edition

Built for an AI voiceover. Each section has three blocks.

**SCREEN** is what you capture or render.
**VOICEOVER** is pure prose, ready to paste into the voice tool with nothing to strip out. Numbers are spelled the way they should be spoken, so the voice does not read "hashtag three three three four one eight".
**MAKE** says whether it is a screen recording or a HyperFrames render.

**No terminal commands anywhere.** The product is the MCP server, so the demo is a maintainer talking to their own assistant. The evaluation evidence, which the tool cannot show because it is not a tool feature, appears as animated graphics instead.

Total voiceover is 746 words. At 150 words per minute that is 296 seconds, and most AI voices run faster, so you have room but not much.

---

## The split, and the time box

Four sections are live screen recordings and cannot be anything else. Four are graphics, and those are the HyperFrames ones.

| Section | Made how |
| --- | --- |
| 1, the problem | HyperFrames |
| 2, memory, free | screen recording |
| 3, the priced menu | screen recording |
| 4, the board | screen recording |
| 5, one submission | screen recording |
| 6, does it work | HyperFrames |
| 7, what I got wrong | HyperFrames |
| 8, the hot take | HyperFrames |

**Time box the HyperFrames work.** If the four graphic sections are not rendering by two hours before the deadline, ship the video with plain static slides for 1, 6, 7 and 8. The voiceover carries those sections; the motion is an improvement, not the substance. A late submission scores zero.

**Build order if time is short:** section 6 first, because an animated number going from 33.3 to 73.3 is the single most persuasive graphic in the video. Then 1, then 8, then 7.

---

## Before you record

**Window width.** 1440 pixels or wider.

**MCP server must be registered.** Confirm with `claude mcp list` and check that `pr-slop` appears. Do this before you record, not on camera.

**Real spend on camera: about 2.80 USD.** One free call, one queue run capped at five submissions (about 2.25), one single deep look (about 0.55).

**The one thing that can go badly wrong.** The priced depth menu only appears when you ask for more than twelve. Ask for five directly and it just spends, and you lose the best moment in the demo. **Ask broadly first**, let it show you the bill, then pick five.

---

# Section 1, zero to twenty five seconds

### MAKE: HyperFrames

### SCREEN

Title card. Suggested motion: a queue of pull request rows stacking up faster than they clear, then the title resolving over them. Keep it restrained, monospace, warm paper background to match the report, one accent.

Fallback if time runs out: a still slide with two job adverts, "open-source contributions" visible in both.

### VOICEOVER (62 words)

```
Every maintainer says a version of the same thing. The pull requests keep coming, more than ever, and a growing share are written by a model. Some are real work. Some are a plausible looking diff with a confident description attached. Both look identical in a list of forty. The expensive part is not merging. It is deciding what to open first.
```

---

# Section 2, twenty five to fifty five seconds. Memory, and it is free.

### MAKE: screen recording

### SCREEN

Your assistant. Type and send:

```
what's new on microsoft/vscode
```

Instant answer: three previous visits, two submissions tracked, and pull request 333390 still in your reading list across two of them. Hold for a beat.

### VOICEOVER (71 words)

```
This is PR slop, and it lives inside the assistant I already use. First question, what changed since last time. That answer was free. No model call, no network, nothing spent. It read what it remembered from the last visit. One submission has now been sitting in my reading list across two visits, which is exactly the thing that gets lost. If nothing is new, there is nothing to pay for.
```

---

# Section 3, fifty five seconds to one forty. It refuses to spend without asking.

### MAKE: screen recording

### SCREEN

Same window. Ask broadly, do not name a number:

```
what should I look at in vscode today
```

It returns the priced depth menu and spends nothing. Hold long enough to read two or three rows including the full-queue price. Then reply:

```
do the five most recent
```

Record it working. Speed this up in the edit.

### VOICEOVER (109 words)

```
Now the real question. What should I look at today. And here is the part I am most pleased with. It did not answer. It came back with a menu, a price against every option, and it has spent nothing.
The whole open queue here is one thousand seven hundred and eighty two pull requests. Reading all of them is about eight hundred dollars of model usage and fourteen hours. A maintainer should see that number before it happens, not after.
So I pick a depth deliberately. Five, for about two dollars. It never spends money without showing me the bill first, and it never offers an option larger than the repository.
```

---

# Section 4, one forty to two twenty five. The board.

### MAKE: screen recording

### SCREEN

Open the page it wrote. Show the three columns. Click into one card, scroll slowly down the detail page, resting on the three evidence blocks and then on the citations block lower down.

### VOICEOVER (109 words)

```
The summary comes back in the chat, and it also writes a page, because chat is a bad place for a table.
Three columns. That is my reading order. Read first, read next, likely to be closed.
Everything is sorted by how much you should trust it, and it says so. Fact is re-derivable without a model. Checked means the model made a claim and we went and verified it. Judgement is the model's opinion with nothing behind it.
And these are the source files it actually opened, at this exact commit, to check that claim. It is not asking you to trust it. It is showing its work.
```

---

# Section 5, two twenty five to three minutes. One submission, in depth.

### MAKE: screen recording

### SCREEN

Back to the assistant:

```
triage pull request 333418 on microsoft/vscode, and review the code
```

About fifty five cents. Hold on the code review, and on the line saying the code does not match its own description.

### VOICEOVER (83 words)

```
And when one submission deserves a proper look, it goes deeper. It reads the pull request, writes its own search against the project's issue tracker, opens the real source at a pinned commit, and a separate reviewer argues with the result before I see any of it.
On this one the judgement says the code does not do what its description claims. That is the most useful thing this tool produces, so it is the loudest mark on the card, not a footnote.
```

---

# Section 6, three minutes to three forty. Does it actually work.

### MAKE: HyperFrames. Build this one first.

### SCREEN

Two animated beats.

**Beat one, the comparison.** A number counting from 33.3 to 73.3 with a labelled floor line at 33.3 held on screen throughout, so the floor and the result are visible together. Label the two bars: "one prompt" and "the shipped agent".

**Beat two, the six versions.** The version table building row by row, with version one and version five highlighted in the accent as they land. Version one is 46.7, worse than the script. Version five drops 27 points.

Source numbers, do not invent any: `README.md` comparison table near the top, and the six-version table in `IMPROVEMENT-CHANGELOG.md`.

### VOICEOVER (110 words)

```
So does it work. There are three piles, so guessing scores thirty three point three percent. A single prompt scored thirty three point three. Exactly a coin toss, and it took a language model to achieve it. The shipped version scores seventy three point three, and finds four times as many of the pile you actually care about.
Six versions got there. Version one was the fully agentic build and it was worse than the plain script I already had. Version five was a change that sounded obviously right and cost twenty seven points. Both are still in the repository, because a changelog with only wins in it is marketing.
```

---

# Section 7, three forty to four twenty. What I got wrong.

### MAKE: HyperFrames

### SCREEN

Three invented figures appearing as published claims, then each one struck through as the real value replaces it. Then a counter running to twelve, with four of those twelve marked in the accent to show they were introduced by fixes.

Keep it plain. The content is damning enough without effects.

### VOICEOVER (100 words)

```
And here is what I got wrong. Three figures I published turned out to be invented. Not wrong. Invented. I wrote numbers no run ever produced, and I only found them because something went back and re-derived every claim from the artifact.
That happened again while I was finishing this. Twelve claims across this repository turned out to be true only in the file that made them. Four of those twelve were introduced by the fix for one of the others. Not one was caught by a test.
Which is the entire thesis of this project, happening to this project.
```

---

# Section 8, four twenty to five minutes. The hot take.

### MAKE: HyperFrames

### SCREEN

The seventeen closed submissions as seventeen marks: four bots, ten insiders, one slop. Let the single slop mark sit alone on screen. Then the three checks appear as a list: names a real problem, source matches the description, how much code and test code.

### VOICEOVER (102 words)

```
The hot take is this. The slop problem is not a writing problem, and you cannot fix it with a better detector.
I read seventeen closed submissions by hand. Four were bots. Ten were insiders. Exactly one looked like slop. The flood everyone is bracing for is mostly not here yet. The real cost today is that good and bad are indistinguishable until somebody reads them.
So this never scores style. It checks three things you can verify, it shows you the evidence for each, and it never acts. It hands you an order to read in. That is the whole product.
```

---

# Production checklist

| # | Duration | Made how | What | Cost |
| --- | --- | --- | --- | --- |
| 1 | 0:25 | HyperFrames | title card, queue stacking up | free |
| 2 | 0:30 | recording | assistant, `what's new on microsoft/vscode` | free |
| 3 | 0:45 | recording | assistant, ask broadly, priced menu, then `do the five most recent` | about 2.25 |
| 4 | 0:45 | recording | browser, the page it wrote, click a card, scroll to citations | free |
| 5 | 0:35 | recording | assistant, `triage pull request 333418 on microsoft/vscode, and review the code` | about 0.55 |
| 6 | 0:40 | HyperFrames | 33.3 to 73.3, then the six-version table | free |
| 7 | 0:40 | HyperFrames | three invented figures struck through, counter to twelve | free |
| 8 | 0:40 | HyperFrames | seventeen marks, then the three checks | free |

**Total spend: about 2.80 USD.**

**Retake insurance.** Sections 3 and 5 cost money each time. Get the framing right on a free call first, then run the paid ones.

**If you run long, cut section 7.** A judge reads the changelog anyway. Do not cut section 3, the priced menu, or the evidence tiers in section 4.

---

# HyperFrames notes

Install once, from anywhere:

```
npx hyperframes skills update
```

Node 24 and ffmpeg 8.1.1 are already on this machine, so there is nothing else to set up.

Then describe each section to your agent. Give it the visual system so the graphics match the report rather than looking bolted on: warm paper background, deep ink text, a single muted gold accent, monospace throughout, no red anywhere, restrained motion. The report at `reports/example-microsoft-vscode.html` is the reference.

**Do not let it invent a number.** Every figure in sections 6, 7 and 8 comes from `README.md` or `IMPROVEMENT-CHANGELOG.md`. Paste the real values into the prompt rather than describing them, and check each rendered frame against the source. This project has produced twelve claims that were true only where they were written; a graphic asserting a number nothing produced would be the thirteenth, on camera.

---

# Voiceover settings

One file per section so you can retime without re-rendering everything. Numbers are already spelled for speech. Do not paste anything from a SCREEN or MAKE block into the voice tool.

Slow the pace slightly for section 3, which carries the most new information, and for the last two sentences of section 8.

---

# The question to be ready for

Not part of the recording. Have it ready if a judge asks live.

A judge who knows the literature may raise Liang and colleagues, 2023, which found seven AI-text detectors flagged over half of ninety one essays by non-native English writers as machine-written, one at nearly ninety eight percent. A tool for spotting machine-written pull requests invites that objection.

> This is not a text detector. It never scores writing style. It scores three checkable things: does the pull request name a problem that is actually in the issue tracker, does the source at a pinned commit match what the description says it does, and how much code and test code is there. Author identity is stripped before the model sees anything. The Liang failure mode is stylometry punishing people who write English differently, and there is no stylometry here. The honest residual risk: the adjudicator is a language model reading the pull request body, so prose style can leak in indirectly, and I have no test for that.

The last sentence is what makes it credible. Do not drop it.

---

# Two things not to overclaim

**"It writes its own search."** True, and scoped to the title. The words it searched for are not in the title, though some appear further down in the body, which may be on screen. The section 5 voiceover avoids the claim entirely. If you ad-lib it, say "from a title with none of these words".

**The fifteen cases.** If a judge raises the sample size, agree first. The repository already says the headline is a tie, that one case moves the number by six point seven points, and that the pre-registered target is unfalsifiable at this sample size. Saying it before they do is worth more than defending it after.
