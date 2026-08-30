#!/usr/bin/env python3
"""Render the shipped agent's step-by-step records.

The agent saves its own trace inside each response as it runs, so unlike the
other two systems these are CAPTURED, not reconstructed afterwards. Every step
below was written while the run was happening.

Four roles appear: the investigator that chooses and judges searches, the claim
checker that reads real source, the adjudicator that decides, and the verifier
that can send work back.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time

import scoring
from harness.trace import Trace, render_index, render_markdown

AGENT_DIR = os.environ.get("PRSLOP_AGENT_DIR", "data/responses/agent-v4")


def main():
    made = 0
    for case in scoring.load_cases():
        n = case["input"]["number"]
        path = f"{AGENT_DIR}/pr-{n}.json"
        if not os.path.exists(path):
            continue
        v = json.load(open(path))
        with Trace("agent", f"triage pull request {n}: investigate the project's "
                            f"recorded problems, check the claim against real "
                            f"source, decide, then verify",
                   capture="captured") as t:
            t.step("read the pull request as handed over", tool="none",
                   args={"case": f"pr-{n}", "fields": sorted(case["input"].keys())},
                   response={"files": len(case["input"].get("changed_files") or []),
                             "patch_chars": len(case["input"].get("patch") or "")})
            for s in v.get("_trace") or []:
                role = s.get("role")
                t.step(f"{role}: {s.get('action')}",
                       tool={"investigator": "search", "claim_checker": "source",
                             "adjudicator": "model", "verifier": "checker"}.get(role, "none"),
                       args={k: s[k] for k in ("query", "round", "corpus_size",
                                               "file", "claims", "attempt")
                             if k in s},
                       response={k: s[k] for k in ("returned", "decision", "matched",
                                                   "why", "supported", "bucket",
                                                   "citations", "reason", "failures",
                                                   "source_chars")
                                 if k in s},
                       retry=("sent back to the adjudicator to redo"
                              if s.get("sending_back") else None),
                       cost=s.get("cost"))
            t.step("human checkpoint", tool="none",
                   checkpoint="the page goes to the maintainer. This system never "
                              "posts, comments, closes or merges anything.")
            t.result = {"status": "ok", "bucket": v.get("bucket"),
                        "truth": case["truth"]["bucket"],
                        "correct": v.get("bucket") == case["truth"]["bucket"],
                        "cost_usd": v.get("_cost"),
                        "search_rounds": v.get("_investigator_rounds")}
        render_markdown(t.run_id)
        made += 1
        # run ids are millisecond timestamps; two cases finishing inside the
        # same millisecond silently overwrote each other. Two of 15 were lost.
        time.sleep(0.002)
    open("traces/INDEX.md", "w").write(render_index())
    print(f"wrote {made} captured trajectory records for the shipped agent")


if __name__ == "__main__":
    main()
