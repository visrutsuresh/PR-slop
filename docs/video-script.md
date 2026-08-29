# Video script, five minutes

Timings are a guide. Everything below is on screen from the real project.

## 0:00 to 0:45, the problem, and why I am the one telling you about it

Open source maintainers are drowning in machine-written pull requests. The curl project says it is "effectively being DDoSed" by them. Around a fifth of its submissions last year were slop. OCaml maintainers rejected a single AI-generated pull request of thirteen thousand lines.

But here is the part most people skip: **why does the slop exist?**

Show two real job adverts I collected during my own internship search.

- Chubb, desirable: "Contribution to open-source AI projects"
- Singtel: "Public portfolio, hackathon wins, open-source contributions"

Employers ask for open source contributions. People who want that line on a CV are pushed to produce volume, and machines make volume nearly free. The slop is not vandalism. It is a rational answer to a hiring signal.

I am not a maintainer. I am the person standing under that pressure, which is why I picked this problem.

## 0:45 to 1:30, the simple version, and its score

Show `./run.sh baseline`.

One prompt per pull request. No tools. This is the comparison the competition brief itself suggests, and I used it rather than a weaker one on purpose.

Result on screen: **33.3 percent**. The floor for three piles is 33.3 percent. It does exactly as well as guessing.

## 1:30 to 3:00, one real run end to end

Take one case. Show the pull request as the system sees it: five fields, nothing else.

Show stage one searching 403 reported problems and returning the correct one first.

Show the model's verdict, with a real reported problem number cited.

Show stage two resolving that number against the project.

Show the human checkpoint. **This tool never posts, comments, closes or merges anything.** It writes a report and a person decides.

## 3:00 to 3:45, the comparison

Show the table.

33.3 to **73.3 percent**. Merge-worthy work wrongly rejected: one in ten, down to zero in ten. Reported problems named that actually exist: one in three, up to nine in nine.

## 3:45 to 4:30, the change that mattered, and the one I removed

**What mattered: search.** Nothing clever. Word overlap, rare words weighted higher. It finds the right reported problem first 78 percent of the time. That single stage is the whole gap.

**What I would have removed: the checking stage.** It struck nothing. Zero across all fifteen. It had nothing to catch, because once search gave the model real problems to point at, it stopped inventing them. I kept it because it costs nothing and the failure it guards against is documented in my own baseline output, but on this evidence stage one did the work, and I am not going to claim otherwise.

**And a mistake I caught in my own measurement.** My first scoring said the simple version cited real evidence 86.7 percent of the time, which appeared to disprove a prediction I had written down in advance. It did not. Twelve of its thirteen valid citations were file paths copied out of the case it had just been handed. That is free. Counting only things that require actually checking, it scored one in three, and my prediction stood. A measure you can satisfy by echoing your own input is not measuring anything.

## 4:30 to 5:00, the honest limit and the hot take

**Where it still fails.** It catches one in five of the not-merged pile, which is the pile the tool exists to find. Accuracy of 73 percent hides that, which is why the per-pile numbers sit next to it everywhere.

**The hot take.** "Closed without merging" looks like it should mean "rejected as bad". On vscode it mostly does not. Of seventeen I inspected, four were bots and about ten were maintainers closing their own real work in favour of another approach. Exactly one looked like slop.

So any triage tool built on free GitHub metadata measures maintainer **behaviour**, not maintainer **judgment of quality**. That is enough to build something useful. It is not the same claim as "this detects AI slop", and I would rather say so than let the number imply otherwise.
