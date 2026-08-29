#!/usr/bin/env python3
"""The simple comparison system: one direct prompt, nothing else.

This is micro1's own first suggested baseline, chosen deliberately over a
cleverer one. It is simple because they named it simple, never crippled on
purpose to make our own system look better.

It is given the pull request and asked for a bucket. It has no way to search
the project's reported problems and no way to read the source, which is exactly
the thing our own system adds and therefore exactly what is being measured.
That difference is declared openly rather than buried.

Two modes:
  --replay    reads the saved responses under data/responses/baseline/ and
              recomputes every published number. No network, no credential,
              no cost. This is what a judge runs.
  --generate  calls the model. Requires the isolation probe to pass first.
              Output WILL differ from ours, because these models are not
              repeatable.
"""
import argparse
import json
import os
import subprocess
import sys
import time

import scoring
import task_spec

RESPONSE_DIR = "data/responses/baseline"
MODEL = "claude-sonnet-5"
DISALLOWED = "Read,Glob,Grep,Bash,WebFetch,WebSearch,Edit,Write,NotebookEdit,Task"
SCRATCH = "/tmp/prslop-gen"
SYSTEM = "You answer with JSON only. No preamble, no markdown fences."


def call_model(prompt: str) -> dict:
    result = subprocess.run(
        ["claude", "-p", prompt, "--model", MODEL,
         "--disallowedTools", DISALLOWED,
         "--append-system-prompt", SYSTEM,
         "--output-format", "json"],
        cwd=SCRATCH, capture_output=True, text=True, timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[:400])
    return json.loads(result.stdout)


def parse_verdict(text: str) -> dict:
    """Pull the JSON verdict out of the reply. A system that returns unparseable
    output is recorded as declining to call, never silently dropped, because
    dropping it would quietly improve the score."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.split("```")[1] if "```" in text[3:] else text
        text = text.lstrip("json").strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return {"bucket": 0, "confidence": "low", "reason": "unparseable reply",
                "citations": [], "_parse_failed": True}
    try:
        d = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return {"bucket": 0, "confidence": "low", "reason": "unparseable reply",
                "citations": [], "_parse_failed": True}
    d.setdefault("citations", [])
    d["bucket"] = int(d.get("bucket", 0) or 0)
    return d


def generate() -> None:
    os.makedirs(RESPONSE_DIR, exist_ok=True)
    os.makedirs(SCRATCH, exist_ok=True)
    for case in scoring.load_cases():
        n = case["input"]["number"]
        path = f"{RESPONSE_DIR}/pr-{n}.json"
        if os.path.exists(path):
            print(f"  pr-{n}: cached, skipping")
            continue
        prompt = task_spec.build_case_prompt(case["input"])
        t0 = time.time()
        envelope = call_model(prompt)
        # The FULL response record is saved, not just the text. A saved file
        # cannot prove a model wrote it, so this is the best available evidence,
        # and it makes "same model on both sides" checkable rather than asserted.
        envelope["_prompt_chars"] = len(prompt)
        envelope["_wall_seconds"] = round(time.time() - t0, 1)
        json.dump(envelope, open(path, "w"), indent=2)
        v = parse_verdict(envelope.get("result", ""))
        print(f"  pr-{n}: bucket {v['bucket']}, {len(v['citations'])} citations, "
              f"{envelope.get('total_cost_usd', 0):.4f} usd")


def replay() -> dict:
    cases = scoring.load_cases()
    truth = {c["input"]["number"]: c["truth"]["bucket"] for c in cases}
    pred, cites, cost, models = {}, {}, 0.0, set()
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
        v = parse_verdict(env.get("result", ""))
        pred[n] = v["bucket"]
        cites[n] = v.get("citations") or []
    if missing:
        print(f"missing saved responses for: {missing}", file=sys.stderr)
        return {}
    cases_by_number = {c["input"]["number"]: c["input"] for c in cases}
    res = scoring.report("baseline, one direct prompt, no repository access",
                         pred, cites, truth, cases_by_number)
    print(f"model(s) used     : {sorted(models)}")
    print(f"measured cost     : {cost:.4f} usd for {len(pred)} cases")
    res["cost_usd"] = round(cost, 4)
    res["models"] = sorted(models)
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
        json.dump(out, open("data/results_baseline.json", "w"), indent=2)
