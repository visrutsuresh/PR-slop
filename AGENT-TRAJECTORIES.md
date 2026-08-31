# Agent trajectories

This file indexes the step-by-step record of what all three systems did across 45 records: the shipped agent (`src/agent_v4.py`) on 15 cases, captured as each run happened, plus 30 reconstructed records for the baseline and the intermediate script: instructions, tool responses, feedback, retries, and the one human checkpoint. It does not duplicate `traces/INDEX.md`, which `src/harness/trace.py` regenerates and which lists every trace file. Read this file first if you want to follow one run end to end.

## The four roles in the loop

Four roles run in sequence on every case.

`investigator` picks what to search for among the project's recorded problems, then judges whether the results actually match. `claim_checker` reads the real source file the investigator pointed at and judges, in isolation, whether the claim holds against the actual code. `adjudicator` decides the pile, act now, worth reviewing, or not merged, from what the investigator found and the claim checker judged. `verifier` checks every citation the adjudicator used against the real repository, and sends a failed citation back to the adjudicator in the same run, before the case is scored.

## Read one, walked through

`traces/agent-1788116123731.md` (pull request 333295) is the exemplar. It renders the instruction the agent received, every tool call, and the final result. It is the only agent trace in this evaluation set where the verifier actually sends work back. The matching `traces/agent-1788116123731.jsonl` holds the same run as raw tool calls and responses, step by step, exactly as `src/harness/trace.py` wrote them to disk.

1. Steps 1 and 2: the investigator searches, then judges the results a match.
2. Step 3: the claim_checker reads the real source and finds the diff does not match what is currently in the repository.
3. Step 4: the adjudicator's first attempt cites `#330142`.
4. Step 5: the verifier fails that citation, `#330142 is not a real recorded problem in this project`, and sends it back. This is the retry.
5. Step 6: the adjudicator's second attempt drops the bad citation and re-decides the pile.
6. Step 7: the verifier checks the new citations and passes.
7. Step 8: the human checkpoint. The page goes to the maintainer. Nothing here posts, comments, closes, or merges anything.

## What ships, counted

`traces/` holds 91 files on disk, and all 91 are tracked: 45 rendered `.md` records, `traces/INDEX.md`, and 45 matching `.jsonl` files with the raw tool calls and model responses behind each record. A judge cloning this repository gets all of it. `SUBMISSION-CHECKLIST.md` states the 45-record figure for the rendered `.md` files; the `.jsonl` count matches it one for one, because `src/harness/trace.py` writes both formats from the same run.
