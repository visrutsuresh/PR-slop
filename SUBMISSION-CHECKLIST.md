# Submission Checklist

Deadline: **2026-08-30 23:59 UTC** (2026-08-30 19:59 EDT). Table timeline + deadline badge value;
prose/header/dashboard state a later Aug 31 18:00 UTC figure — plan against the earlier one, see
`Meta` project note `Timeline.md` for the full contradiction record.

FAQ valid-submission bar: "repository, archive, tests, README, agent-use evidence, and demo video."

- [ ] **1. Solution code + Improvement Changelog** — `README.md` (intended user, bottleneck, value,
      failure mode, hot take) + `CHANGELOG.md` (one entry per iteration, tied to evidence)
- [ ] **2. Reproduction guide** — `docs/reproduction.md`
- [ ] **3. Solution video, ≤5:00** — beat sheet at `docs/video-script.md`; final file linked in `README.md`
- [ ] **4. Agent trajectories** — `traces/INDEX.md` (every agent used), `traces/*.md` (representative runs)
- [ ] **4a. Trajectories are actually committed** — `traces/*.jsonl` stays gitignored (raw pre-redaction
      risk), but `traces/*.md` and `traces/INDEX.md` are tracked; verify from a FRESH CLONE that
      `git show HEAD:traces/INDEX.md` and at least one `traces/<run_id>.md` return content, not
      "not found"
- [ ] **Judge access** — repo is reachable by the judges (public, or judges added as collaborators)
      before the deadline; rule book item 10: "Give judges enough access to run the project and
      reproduce the main result." A private repo with no judge access is disqualified before scoring.
- [ ] **Actually submitted on the platform** — the repo link, archive, and video are submitted through
      the micro1 portal before 2026-08-30 23:59 UTC; only the latest complete submission is evaluated
- [ ] **Archive** — zip or tarball of the repo at submission time (FAQ, not on the 4 cards)
- [ ] **Tests** — `python3 test_harness.py` passes; solution-specific tests once written
- [ ] **Tool disclosure** — `README.md` § Tools disclosure, names every agent/model/tool used
- [ ] **PRE-EXISTING.md** — updated with anything reused after kickoff
- [ ] **`run.sh baseline` / `advanced` / `eval`** all run clean from a fresh clone
