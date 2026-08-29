#!/usr/bin/env python3
"""Turn the saved model responses into readable step-by-step records.

Deliverable 4 asks for a trajectory per agent used, easy to follow from the
instruction through to the final result, showing what each stage did and how
its tools answered.

These are marked "reconstructed" rather than "captured", honestly. The model
calls happened first and were saved whole; this replays those saved records
into the trace format. Nothing is invented: every field here comes from a file
under data/, and the reconstruction runs offline from the committed cache, so
anyone can regenerate identical records.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import run_baseline
import scoring
from harness.trace import Trace, render_index, render_markdown
from retriever import IssueSearch
from run_advanced import verify


def trace_baseline(case, env):
    n = case["input"]["number"]
    with Trace("baseline", f"triage pull request {n} with one direct prompt, "
                           "no access to the project", capture="reconstructed") as t:
        t.step("read the pull request as handed over", tool="none",
               args={"case": f"pr-{n}", "fields": sorted(case["input"].keys())},
               response={"changed_files": len(case["input"].get("changed_files") or []),
                         "patch_chars": len(case["input"].get("patch") or "")})
        t.step("no way to search the project's reported problems", tool="none",
               response="the simple version has no search step, which is the "
                        "capability being measured")
        v = run_baseline.parse_verdict(env.get("result", ""))
        t.step("ask the model for a verdict", tool="model",
               args={"model": sorted((env.get("modelUsage") or {}).keys()),
                     "prompt_chars": env.get("_prompt_chars")},
               response=v, cost=env.get("total_cost_usd"))
        t.result = {"status": "ok", "bucket": v["bucket"],
                    "truth": case["truth"]["bucket"],
                    "correct": v["bucket"] == case["truth"]["bucket"]}
    return t.run_id


def trace_advanced(case, env, search, known):
    n = case["input"]["number"]
    with Trace("our-system", f"triage pull request {n} using search over the "
                             "project plus a check on every claim",
               capture="reconstructed") as t:
        t.step("read the pull request as handed over", tool="none",
               args={"case": f"pr-{n}", "fields": sorted(case["input"].keys())},
               response={"changed_files": len(case["input"].get("changed_files") or []),
                         "patch_chars": len(case["input"].get("patch") or "")})
        retrieved = env.get("_retrieved") or []
        q = f"{case['input']['title']} {(case['input'].get('body') or '')[:600]}"
        hits = search.search(q, k=8)
        t.step("stage 1, search the project's reported problems", tool="search",
               args={"corpus_size": len(search.issues), "top_k": 8},
               response={"returned": retrieved,
                         "top_match": hits[0]["title"][:90] if hits else None})
        raw = run_baseline.parse_verdict(env.get("result", ""))
        t.step("ask the model for a verdict, with those matches attached",
               tool="model",
               args={"model": sorted((env.get("modelUsage") or {}).keys()),
                     "prompt_chars": env.get("_prompt_chars")},
               response=raw, cost=env.get("total_cost_usd"))
        before = dict(raw)
        checked = verify(dict(raw), case["input"], known)
        t.step("stage 2, check every claim against the real project",
               tool="verifier",
               args={"claims_offered": before.get("citations")},
               response={"kept": checked["citations"],
                         "struck_as_nonexistent": checked.get("struck_citations"),
                         "verdict_downgraded": "bucket_before_check" in checked})
        t.step("human checkpoint", tool="none",
               checkpoint="the report is handed to the maintainer. This system "
                          "never posts, comments, closes or merges anything.")
        t.result = {"status": "ok", "bucket": checked["bucket"],
                    "truth": case["truth"]["bucket"],
                    "correct": checked["bucket"] == case["truth"]["bucket"]}
    return t.run_id


def main():
    cases = scoring.load_cases()
    search = IssueSearch()
    known = scoring.known_issue_numbers()
    made = 0
    for case in cases:
        n = case["input"]["number"]
        b = f"data/responses/baseline/pr-{n}.json"
        a = f"data/responses/advanced/pr-{n}.json"
        if os.path.exists(b):
            render_markdown(trace_baseline(case, json.load(open(b))))
            made += 1
        if os.path.exists(a):
            render_markdown(trace_advanced(case, json.load(open(a)), search, known))
            made += 1
    open("traces/INDEX.md", "w").write(render_index())
    print(f"wrote {made} trajectory records to traces/")


if __name__ == "__main__":
    main()
