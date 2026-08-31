# Video production record

**The film is made.** This file is the record of how, not instructions to follow.

- **The film:** `docs/video/film.mp4`, 4 minutes 54.87 seconds, 1920x1080, 30fps, no audio.
- **The narration to record:** `docs/voiceover-sheet.md`. Eight blocks, timed to the frames. That file supersedes everything below.

## What was made, and how

Eight sections. Four animate a real session, four are rendered graphics.

| Section | Starts | Runs | Made how |
| --- | --- | --- | --- |
| 1 | 0:00.0 | 26.3s | HyperFrames graphic |
| 2 | 0:26.3 | 29.0s | animated from a real session |
| 3 | 0:55.3 | 40.0s | animated from a real session |
| 4 | 1:35.3 | 40.0s | animated from the generated report |
| 5 | 2:15.3 | 32.0s | animated from the generated report |
| 6 | 2:47.3 | 45.5s | HyperFrames graphic |
| 7 | 3:32.8 | 41.5s | HyperFrames graphic |
| 8 | 4:14.3 | 42.3s | HyperFrames graphic |

**The session in sections 2 and 3** ran on 2026-08-31 at 14:52 UTC, in Claude Code, against `microsoft/vscode` through the MCP server. The assistant was asked what was new (free, no model call), then what to look at today. It refused to scan without showing the bill, offered a priced menu, and ran ten submissions for 3.70 USD at a quoted 0.45 each. It flagged `#333508` for referencing a `todoFeature.ts` module that does not exist, carrying placeholder comments in another language, and shipping no tests, closing with "Don't trust the description."

**Sections 4 and 5** are rendered from the HTML report that run produced, captured at 4800 pixels wide so the camera moves stay sharp. That page is not committed, because `reports/` is gitignored apart from the example; regenerate it by pointing the tool at a repository yourself, or open the committed `reports/example-microsoft-vscode.html` to see the same layout.

**Sections 1, 6, 7 and 8** are built with HyperFrames from HTML. Every figure in them is read from `README.md` or `IMPROVEMENT-CHANGELOG.md`.

Nothing on screen was invented for the film.

## The question to be ready for

Not in the film. Have it ready if a judge asks live.

A judge who knows the literature may raise Liang and colleagues, 2023, which found seven AI-text detectors flagged over half of ninety one essays by non-native English writers as machine-written, one at nearly ninety eight percent. A tool for spotting machine-written pull requests invites that objection.

> This is not a text detector. It never scores writing style. It scores three checkable things: does the pull request name a problem that is actually in the issue tracker, does the source at a pinned commit match what the description says it does, and how much code and test code is there. Author identity is stripped before the model sees anything. The Liang failure mode is stylometry punishing people who write English differently, and there is no stylometry here. The honest residual risk: the adjudicator is a language model reading the pull request body, so prose style can leak in indirectly, and I have no test for that.

The last sentence is what makes it credible. Do not drop it.

## Two things not to overclaim

**"It writes its own search."** True, and scoped to the title. The words it searched for are not in the title, though some appear further down in the body. The film does not make the claim; if you make it live, say "from a title with none of these words".

**The fifteen cases.** If a judge raises the sample size, agree first. The repository already says the headline is a tie, that one case moves the number by six point seven points, and that the pre-registered target is unfalsifiable at this sample size. Saying it before they do is worth more than defending it after.
