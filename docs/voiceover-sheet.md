# Voiceover sheet, timed to the cut

Each block below is written against the actual frames, so the words land on the picture rather than near it. Paste each fenced block into the voice tool as one file. Nothing else on this page goes into the voice tool.

**Film:** `/tmp/prslop-video/out/FILM.mp4`, 4 minutes 54.87 seconds, 1920x1080, 30fps, no audio.

**Read speed: 150 words per minute.** Every block is sized to its section at that rate. If your voice runs fast, put the slack into the pause before the last sentence, not into speaking sooner.

| Section | Starts | Runs | Words | Covers |
| --- | --- | --- | --- | --- |
| 1 | 0:00.0 | 26.3s | 61 | the problem |
| 2 | 0:26.3 | 29.0s | 66 | memory, and it is free |
| 3 | 0:55.3 | 40.0s | 88 | refuses to spend, then finds the slop |
| 4 | 1:35.3 | 40.0s | 104 | the board |
| 5 | 2:15.3 | 32.0s | 75 | one submission in depth |
| 6 | 2:47.3 | 45.5s | 105 | does it actually work |
| 7 | 3:32.8 | 41.5s | 98 | what I got wrong |
| 8 | 4:14.3 | 42.3s | 102 | the hot take |

699 words, 280 seconds at 150 wpm, against 294.87 seconds of picture.

**The 15 second difference is deliberate silence, not a shortfall.** Two shots are meant to play with nothing spoken over them. Section 3 holds on "Don't trust the description." for its last ten seconds. Section 6 holds on the closing line. Do not write extra words to fill those; the silence is the emphasis.

---

## Section 1, 26.3 seconds, 61 words

```
Every maintainer says a version of the same thing. The pull requests keep coming, more than ever, and a growing share are written by a model. Some are real work. Some are a plausible looking diff with a confident description. Both look identical in a list of forty. The expensive part is not merging. It is deciding what to open first.
```

---

## Section 2, 29.0 seconds, 66 words

```
This is PR slop, and it lives inside the assistant I already use. First question. What changed since last time. That answer was free. No model call, no network, nothing spent. It read what it remembered. Seven submissions are still sitting in my reading list from earlier visits, which is exactly the thing that gets lost. If nothing is new, there is nothing to pay for.
```

---

## Section 3, 40.0 seconds, 88 words

Beats: typing starts at 0, the price refusal lands at 3, the scan-scope menu builds 9 to 15, the scan runs at 18, the cost counts up and settles on three dollars seventy at 24, `#333508` appears at 27, and **"Don't trust the description."** lands at 30 and holds to the end. Do not rush the last two sentences.

```
Now the real question. What should I look at today. And here is the part I am most pleased with. It did not answer. It came back with a menu, a price against every option, and it had spent nothing.
So I choose. Ten submissions. Three dollars seventy.
And look at the last one. It references a module that does not exist. Placeholder comments in another language. No tests. The tool does not hedge about it. It tells me not to trust the description, and it is right.
```

---

## Section 4, 40.0 seconds, 104 words

Beats: the board establishes, then each column header, then one card's evidence chips, then `#333508` and its flag.

```
The summary comes back in the chat, and it writes a page, because chat is a bad place for a table.
Three columns, and that is my reading order. Read first. Read next. Likely to be closed.
Every card carries how much you should trust it. How many plain facts. How many claims we went and checked. How many are only opinion.
And then this one. It put that submission in the skip pile, and told me in the same breath that the evidence is stronger than that pile suggests. It argues with its own ranking, which is more than most tools will do.
```

---

## Section 5, 32.0 seconds, 75 words

```
And when one submission deserves a proper look, it goes deeper. It reads the pull request, writes its own search against the project's issue tracker, and opens the real source at a pinned commit.
These are the files it actually opened to check the claim. Not a summary of them. The files. Click one and you land on the line it read. It is not asking you to trust it. It is showing its work.
```

---

## Section 6, 45.5 seconds, 105 words

Beats: the floor line draws at 0, the first bar reaches 33.3 at 6, the second climbs to 73.3 by 12, a punch on the number at 13, then the table builds a row every three seconds from 21, closing on the marketing line at 39.

```
So does it work. There are three piles, so guessing scores thirty three point three percent. That dashed line is the floor.
A single prompt scored thirty three point three. It landed exactly on the floor. A coin toss, and it took a language model to achieve it.
The shipped version scores seventy three point three.
Six versions got there. The first real agent was worse than the plain script I already had. Version five made the investigator's verdict binding, which sounded obviously right, and cost twenty seven points. Both are still in the repository, because a changelog with only wins in it is marketing.
```

---

## Section 7, 41.5 seconds, 98 words

```
And here is what I got wrong. Three figures I published turned out to be invented. Not wrong. Invented. I wrote numbers that no run ever produced.
I only found them because something went back and re-derived every claim from the artifact, one at a time, instead of reading the sentence and believing it.
Six entries in this changelog exist only to record the project being wrong. They are the ones worth reading.
And not one of them was found by a test I had written in advance. Every single one was caught afterwards, by going and looking.
```

---

## Section 8, 42.3 seconds, 102 words

```
The hot take is this. The slop problem is not a writing problem, and you cannot fix it with a better detector.
I read seventeen closed submissions by hand. Four were bots. Ten were insiders. Exactly one looked like slop. The flood everyone is bracing for is mostly not here yet. The real cost today is that good and bad are indistinguishable until somebody reads them.
So this never scores style. It checks three things you can verify, it shows you the evidence for each, and it never acts. It hands you an order to read in. That is the whole product.
```

---

## Every number here is from the live run

The film animates a real Claude Code session against `microsoft/vscode`, run 2026-08-31 at 14:52 UTC through the MCP server.

Ten submissions scanned. Three dollars seventy spent, quoted at forty five cents each. Seven already flagged from earlier visits. Two minutes ten seconds of scan time. `#333508` referencing a nonexistent `todoFeature.ts`, with placeholder comments in another language and no tests.

The evaluation figures are from the repository: thirty three point three percent floor, seventy three point three shipped, six versions, version five costing twenty seven points, three invented figures, six changelog entries recording the project being wrong, seventeen closed submissions read by hand.

Nothing on screen was invented for the film.
