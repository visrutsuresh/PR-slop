#!/usr/bin/env python3
"""Our system. Same model, same instructions, same fifteen cases as the simple
comparison version. The difference is what it can reach.

Built one stage at a time, each added only after a measurement showed it was
needed. See IMPROVEMENT-CHANGELOG.md for what each stage changed and why.

  stage 1  search      the project's reported problems are searched, and the
                       best matches are put in front of the model. This is the
                       thing a single prompt cannot do: there are hundreds of
                       reported problems and they do not fit in one prompt.
  stage 2  check       every claim the model makes is checked against the real
                       project. Anything pointing at something that does not
                       exist is struck out rather than trusted.

Two modes, same as the baseline. --replay reads saved answers and recomputes
every published number offline. --generate calls the model.
"""
import argparse
import json
import os
import subprocess
import sys
import time

import scoring
import task_spec
from retriever import IssueSearch

RESPONSE_DIR = "data/responses/advanced"
MODEL = "claude-sonnet-5"
DISALLOWED = "Read,Glob,Grep,Bash,WebFetch,WebSearch,Edit,Write,NotebookEdit,Task"
SCRATCH = "/tmp/prslop-gen"
SYSTEM = "You answer with JSON only. No preamble, no markdown fences."
STAGE = 2


def call_model(prompt: str) -> dict:
    r = subprocess.run(
        ["claude", "-p", prompt, "--model", MODEL,
         "--disallowedTools", DISALLOWED,
         "--append-system-prompt", SYSTEM,
         "--output-format", "json"],
        cwd=SCRATCH, capture_output=True, text=True, timeout=300,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr[:400])
    return json.loads(r.stdout)


def build_prompt(case_input: dict, hits: list[dict]) -> str:
    base = task_spec.build_case_prompt(case_input)
    if hits:
        lines = "\n".join(
            f"  #{h['number']}  {h['title'][:110]}\n      {h['excerpt'][:200]}"
            for h in hits
        )
        found = (
            "\n--- reported problems already open in this project that look "
            "related ---\n"
            "These were found by searching the project. They may or may not be "
            "what this pull request answers. Judge for yourself. If one of them "
            "is genuinely what this work fixes, cite it as #NNNNN and use it to "
            "support bucket 1. If none of them really matches, say so and do NOT "
            "cite one anyway.\n\n" + lines + "\n"
        )
    else:
        found = "\n--- no related reported problems were found by searching ---\n"
    return base + found


def verify(verdict: dict, case_input: dict, known_issues: set) -> dict:
    """Stage 2. Strike out anything the model pointed at that does not exist.

    A maintainer's real fear is not a wrong label, it is a confident claim that
    turns out to be made up. So every reference is resolved against the real
    project before it is shown. Anything that does not resolve is removed and
    recorded, never silently kept.
    """
    import re
    own = set(case_input.get("changed_files") or [])
    kept, struck = [], []
    for c in verdict.get("citations") or []:
        c = str(c).strip()
        m = re.fullmatch(r"#(\d+)", c)
        if m:
            (kept if int(m.group(1)) in known_issues else struck).append(c)
        elif c in own:
            kept.append(c)
        else:
            struck.append(c)
    verdict["citations"] = kept
    verdict["struck_citations"] = struck
    # If the call rested on a reference that turned out not to exist, the
    # evidence for it is gone, so the confident answer is downgraded rather
    # than left standing.
    if struck and verdict.get("bucket") == 1 and not any(
            c.startswith("#") for c in kept):
        verdict["bucket_before_check"] = verdict["bucket"]
        verdict["bucket"] = 0
        verdict["reason"] = (verdict.get("reason", "") +
                             " [downgraded: the reported problem it named does not exist]")
    return verdict


def generate() -> None:
    os.makedirs(RESPONSE_DIR, exist_ok=True)
    os.makedirs(SCRATCH, exist_ok=True)
    search = IssueSearch()
    for case in scoring.load_cases():
        n = case["input"]["number"]
        path = f"{RESPONSE_DIR}/pr-{n}.json"
        if os.path.exists(path):
            print(f"  pr-{n}: cached, skipping")
            continue
        q = f"{case['input']['title']} {(case['input'].get('body') or '')[:600]}"
        hits = search.search(q, k=8)
        prompt = build_prompt(case["input"], hits)
        t0 = time.time()
        env = call_model(prompt)
        env["_retrieved"] = [h["number"] for h in hits]
        env["_prompt_chars"] = len(prompt)
        env["_wall_seconds"] = round(time.time() - t0, 1)
        env["_stage"] = STAGE
        json.dump(env, open(path, "w"), indent=2)
        print(f"  pr-{n}: retrieved {len(hits)}, "
              f"{env.get('total_cost_usd', 0):.4f} usd")


def replay() -> dict:
    import run_baseline
    cases = scoring.load_cases()
    truth = {c["input"]["number"]: c["truth"]["bucket"] for c in cases}
    by_num = {c["input"]["number"]: c["input"] for c in cases}
    known = scoring.known_issue_numbers()
    pred, cites, cost, models, struck = {}, {}, 0.0, set(), 0
    missing = []
    for c in cases:
        n = c["input"]["number"]
        path = f"{RESPONSE_DIR}/pr-{n}.json"
        if not os.path.exists(path):
            missing.append(n)
            continue
        env = json.load(open(path))
        cost += env.get("total_cost_usd") or 0.0
        models.update((env.get("modelUsage") or {}).keys())
        v = run_baseline.parse_verdict(env.get("result", ""))
        v = verify(v, by_num[n], known)
        struck += len(v.get("struck_citations") or [])
        pred[n] = v["bucket"]
        cites[n] = v["citations"]
    if missing:
        print(f"missing saved responses for: {missing}", file=sys.stderr)
        return {}
    res = scoring.report("our system, search plus checking", pred, cites, truth, by_num)
    print(f"struck as made up : {struck} references removed by the check")
    print(f"model(s) used     : {sorted(models)}")
    print(f"measured cost     : {cost:.4f} usd for {len(pred)} cases")
    res.update({"cost_usd": round(cost, 4), "models": sorted(models),
                "struck_citations": struck, "stage": STAGE})
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--generate", action="store_true")
    ap.add_argument("--replay", action="store_true")
    a = ap.parse_args()
    if a.generate:
        generate()
    out = replay()
    if out:
        json.dump(out, open("data/results_advanced.json", "w"), indent=2)
