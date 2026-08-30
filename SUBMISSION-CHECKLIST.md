# Submission checklist

**Deadline: Monday 2026-08-31, 18:00 UTC. That is Mon 14:00 EDT, Tue 02:00 SGT.**

This was contradictory earlier and is now settled: the live page shows Aug 31 18:00 UTC in the timeline table AND in the deadline badge, and Aug 30 23:59 UTC is labelled only a checkpoint. An earlier version of this file carried the Aug 30 value. It was wrong.

"Late or incomplete entries are not accepted", and a validation screen for reproducibility, plagiarism and trace integrity runs afterwards. **An entry that lands at 17:59 but does not run on a judge's machine still fails.** Do not plan to finish at the deadline.

---

## Done

- [x] **1. Solution code plus Improvement Changelog.** `README.md` names the intended user, the bottleneck, why it matters, where it still fails, and the hot take. `CHANGELOG.md` has one entry per real iteration, each tied to evidence, including the experiments that were removed and the three made-up numbers that were caught.
- [x] **2. Reproduction guide.** `docs/reproduction.md`. Verified by cloning fresh into an empty folder and running with only `/usr/bin` on the path: no account, no network, no cost, and the numbers reproduce exactly.
- [x] **4. Agent trajectories.** 45 records in `traces/`, covering all three systems. The shipped agent's 15 are marked **captured**, written as each run happened. The other 30 are marked **reconstructed** from committed responses. `traces/INDEX.md` lists them.
- [x] **Tests.** `python3 test_harness.py` 10/10, `python3 test_harvest.py` 15/15. Includes an anti-leak suite with a positive control, proven to fail when a leak is planted.
- [x] **Tool disclosure.** `README.md`, naming the model, how it is called, and the isolation applied to it.
- [x] **PRE-EXISTING.md.** Timestamp-based, so it stays true as later commits land.
- [x] **Every command runs clean from a fresh clone.** `triage`, `baseline`, `script`, `agent`, `eval`, all offline.

## Still to do

- [ ] **3. Solution video, 5:00 or under.** Script and shot list at `docs/video-script.md`. Done when the file exists and is linked from `README.md`.
- [ ] **Judge access. THIS IS THE ONE THAT DISQUALIFIES YOU.** The repository is currently **PRIVATE**. Rule 10 requires judges to be able to run it. Make it public, or add the judges as collaborators, **before** the deadline. A private repository is thrown out before anyone reads a line of the work.
- [ ] **Archive.** A zip or tarball taken at submission time. Required by the FAQ even though it is not one of the four deliverable cards.
- [ ] **Actually submitted on the micro1 platform.** Repository link, archive and video, all through the portal. Only the most recent complete submission counts, so a half-finished late resubmission can overwrite a good earlier one.

## Final checks, five minutes, in this order

1. `git push`, and confirm the remote actually has the latest commit.
2. Flip the repository to public.
3. Clone the public URL into a fresh empty folder, exactly as a stranger would.
4. In that clone run `./run.sh eval`, `./run.sh agent`, `./run.sh triage`.
5. Confirm `git show HEAD:traces/INDEX.md` prints real content, so the records are in the repository and not merely on your machine.
