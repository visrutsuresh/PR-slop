# Voiceover sheet, timed to the cut

Every block below is rewritten so the words land on the picture. Paste each fenced block into the voice tool as one file. Nothing else on this page goes into the voice tool.

**Film:** `/tmp/prslop-video/out/full.mp4`, 4 minutes 54.87 seconds, 1920x1080, 30fps, no audio.

**Read speed: 150 words per minute.** Every block is sized to its section at that rate. If your voice runs faster, add the slack as a pause before the last sentence rather than speaking sooner.

| Section | Starts at | Runs | Words | Covers |
| --- | --- | --- | --- | --- |
| 1 | 0:00.0 | 26.3s | 65 | the problem |
| 2 | 0:26.3 | 29.0s | 72 | memory, free |
| 3 | 0:55.3 | 40.0s | 99 | refuses to spend, then the slop |
| 4 | 1:35.3 | 40.0s | 99 | the board |
| 5 | 2:15.3 | 32.0s | 79 | one submission in depth |
| 6 | 2:47.3 | 45.5s | 113 | does it work |
| 7 | 3:32.8 | 41.5s | 103 | what I got wrong |
| 8 | 4:14.3 | 42.3s | 105 | the hot take |

Total 735 words, 294 seconds at 150 wpm, against 294.87 seconds of picture.

---

## Section 1, 26.3 seconds, 65 words

```
Every maintainer says a version of the same thing. The pull requests keep coming, more than ever, and a growing share are written by a model. Some are real work. Some are a plausible looking diff with a confident description. Both look identical in a list of forty. The expensive part is not merging. It is deciding what to open first.
```

---

## Section 2, 29.0 seconds, 72 words

Beats: the prompt types in at about 3 seconds, the answer reveals from about 8, the punch onto the two tracked pull request numbers lands around 14.

```
This is PR slop, and it lives inside the assistant I already use. First question. What changed since last time. That answer was free. No model call, no network, nothing spent. It read what it remembered from the last visit. Two submissions have been sitting in my reading list across visits, which is exactly the thing that gets lost. If nothing is new, there is nothing to pay for.
```

---

## Section 3, 40.0 seconds, 99 words

Beats, and the words are placed against them: the refusal lands at about 10, the priced menu is on screen 11 to 15, the figure of one dollar eighty eight lands at about 18, and the Turkish comments line is on screen at about 26. **Do not speak faster than the picture here.** The last two sentences are the point of the section.

```
Now the real question. What should I look at today. And here is the part I am most pleased with. It did not answer. It came back with a menu, a price against every option, and it had spent nothing.
So I pick a depth. Five submissions. It quoted me about two dollars twenty five and it spent one dollar eighty eight.
And look at the last one. Code that does not match its own description. Turkish comments left in the file. No tests. That is the thing I built this to find, and it found it on the first real run.
```

---

## Section 4, 40.0 seconds, 99 words

**This block is rewritten.** The old one described the citations block, which is section 5's footage. Beats here: stat tiles at about 3, the three column headers at about 6, one card's evidence chips at about 10, and `#333508` with its flag landing at about 16.

```
The summary comes back in the chat, and it writes a page, because chat is a bad place for a table.
Five submissions. Six follow up searches it chose to run. One dollar eighty eight.
Three columns, and that is my reading order. Read first. Read next. Likely to be closed.
Every card carries how much you should trust it. How many plain facts. How many claims we checked. How many are just opinion.
And then this. It put that one in the skip pile, and told me in the same breath that the evidence is stronger than that pile suggests. It argues with its own ranking.
```

---

## Section 5, 32.0 seconds, 79 words

```
And when one submission deserves a proper look, it goes deeper. It reads the pull request, writes its own search against the project's issue tracker, and opens the real source at a pinned commit.
These are the files it actually opened to check the claim. Not a summary of them. The files. Click one and you land on the line it read. It is not asking you to trust it. It is showing its work.
```

---

## Section 6, 45.5 seconds, 113 words

```
So does it work. There are three piles, so guessing scores thirty three point three percent. A single prompt scored thirty three point three. Exactly a coin toss, and it took a language model to achieve it.
The shipped version scores seventy three point three, and finds four times as many of the pile you actually care about.
Six versions got there. Version one was the fully agentic build, and it was worse than the plain script I already had. Version five was a change that sounded obviously right, and it cost twenty seven points. Both are still in the repository, because a changelog with only wins in it is marketing.
```

---

## Section 7, 41.5 seconds, 103 words

```
And here is what I got wrong. Three figures I published turned out to be invented. Not wrong. Invented. I wrote numbers that no run ever produced.
I only found them because something went back and re-derived every claim from the artifact, one at a time, instead of reading the sentence and believing it.
Six entries in this changelog exist only to record the project being wrong. They are the ones worth reading.
And not one of them was found by a test I had written in advance. Every single one was caught after the fact, by going and looking.
```

---

## Section 8, 42.3 seconds, 105 words

```
The hot take is this. The slop problem is not a writing problem, and you cannot fix it with a better detector.
I read seventeen closed submissions by hand. Four were bots. Ten were insiders. Exactly one looked like slop. The flood everyone is bracing for is mostly not here yet. The real cost today is that good and bad are indistinguishable until somebody reads them.
So this never scores style. It checks three things you can verify, it shows you the evidence for each, and it never acts. It hands you an order to read in. That is the whole product.
```

---

## What changed, and why

**Section 4 was describing the wrong screen.** The original block explained the three evidence tiers and the citations block. Neither is in section 4's footage; both are in section 5. It now describes what is actually on screen: the stat tiles, the column headers, the per-card trust counts, and the `#333508` flag.

**Section 3 was missing its best moment.** The Turkish comments and the no-tests line are on screen at 26 seconds and the script never mentioned them. That is real AI slop caught on a live queue, so it now closes the section.

**Section 5 lost the tier explanation and gained the citations.** The tiers moved to section 4 where the chips are, and section 5 now carries the source files, which is what its footage shows.

**Every number is real and matches the frame.** One dollar eighty eight was the actual spend. Two dollars twenty five was the quote. Five submissions, six follow up searches, seventeen closed submissions read by hand, three invented figures, six entries recording the project being wrong.
