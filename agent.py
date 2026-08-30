#!/usr/bin/env python3
"""The agent. Three roles, a real loop, and a verifier that sends work back.

WHY THIS EXISTS. The first version of this project was a script: search once,
ask a model once, run a regex over the answer. That is a form, not an agent.
Nothing in it ever decided anything. The model never chose what to look for,
never asked for more, and never acted twice.

What is different here:

  1. INVESTIGATOR decides what to search for, reads what comes back, and can
     search AGAIN with better wording if the first attempt was poor. It is the
     one choosing the action, not us.

  2. CLAIM CHECKER reads the actual source at a pinned commit and tests whether
     the submission does what it says. Previously we only checked that a
     complaint NUMBER existed, never whether the claim about the code was true.

  3. ADJUDICATOR decides the pile, using what the other two found.

  4. VERIFIER checks every claim and, when something does not hold up, SENDS IT
     BACK. The adjudicator revises with the failure in hand. Previously a failed
     claim was silently deleted and nothing reconsidered.

Every model call runs isolated: empty directory outside the project, no file
access, no shell, no network. The source the claim checker reads is fetched by
US and handed over as text, so the model still cannot go looking for answers.
"""
import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time

import scoring
import task_spec
from retriever import IssueSearch

RESPONSE_DIR = "data/responses/agent"
MODEL = "claude-sonnet-5"
DISALLOWED = "Read,Glob,Grep,Bash,WebFetch,WebSearch,Edit,Write,NotebookEdit,Task"
SCRATCH = "/tmp/prslop-gen"
MAX_SEARCH_ROUNDS = 2
MAX_REVISIONS = 1

SYSTEMS = {
    "investigator": "You are deciding what to look for. Reply with JSON only.",
    "claim_checker": "You are checking claims against real code. Reply with JSON only.",
    "adjudicator": "You are making a triage decision. Reply with JSON only.",
}


def call(prompt, role):
    """One isolated model call. The role shapes only the instruction; every
    role gets the same locked-down environment."""
    r = subprocess.run(
        ["claude", "-p", prompt, "--model", MODEL,
         "--disallowedTools", DISALLOWED,
         "--append-system-prompt", SYSTEMS[role] + " No preamble, no fences.",
         "--output-format", "json"],
        cwd=SCRATCH, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[:300])
    return json.loads(r.stdout)


def parse(text, fallback):
    text = (text or "").strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        text = text.lstrip("json").strip()
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b <= a:
        return dict(fallback)
    try:
        return json.loads(text[a:b + 1])
    except json.JSONDecodeError:
        return dict(fallback)


INVESTIGATOR = """A code submission has arrived for the VS Code project. Before anyone
judges it, work out whether it answers a problem somebody already reported.

You cannot browse. You ask, and a search runs for you over the project's
recorded problems.

%(history)s
Submission title: %(title)s

Description:
%(body)s

Files it changes:
%(files)s

Decide what to search for. Use the words a person REPORTING this problem would
have used, which are often not the words a developer FIXING it would use.

Reply as JSON:
{"query": "the words to search for",
 "looking_for": "what a genuine match would look like, one sentence"}"""

FOLLOWUP = """Your search for "%(query)s" returned these:

%(results)s

Judge them. If one is genuinely the problem this submission fixes, stop. If none
really matches, and different wording would plausibly do better, search again.

Reply as JSON:
{"decision": "stop" or "search_again",
 "matched_issue": 12345 or null,
 "why": "one sentence",
 "next_query": "different words, only if searching again"}"""


def investigate(ci, search, trace):
    files = "\n".join("  " + p for p in (ci.get("changed_files") or [])[:25]) or "  (none)"
    history, query, matched = "", None, None
    for rnd in range(1, MAX_SEARCH_ROUNDS + 1):
        if query is None:
            env = call(INVESTIGATOR % {
                "history": history, "title": ci.get("title"),
                "body": (ci.get("body") or "(none)")[:1800], "files": files},
                "investigator")
            plan = parse(env.get("result", ""), {"query": ci.get("title") or ""})
            query = plan.get("query") or ci.get("title") or ""
            trace.append({"role": "investigator", "action": "chose a search",
                          "round": rnd, "query": query,
                          "looking_for": plan.get("looking_for"),
                          "cost": env.get("total_cost_usd")})
        hits = search.search(query, k=8)
        listing = "\n".join("  #%d  %s" % (h["number"], h["title"][:100])
                            for h in hits) or "  (nothing found)"
        env2 = call(FOLLOWUP % {"query": query, "results": listing}, "investigator")
        v = parse(env2.get("result", ""), {"decision": "stop", "matched_issue": None})
        trace.append({"role": "investigator", "action": "judged the results",
                      "round": rnd, "returned": [h["number"] for h in hits],
                      "decision": v.get("decision"), "matched": v.get("matched_issue"),
                      "why": v.get("why"), "cost": env2.get("total_cost_usd")})
        matched = v.get("matched_issue")
        if v.get("decision") != "search_again" or rnd == MAX_SEARCH_ROUNDS:
            return {"query": query, "hits": hits, "matched_issue": matched, "rounds": rnd}
        history = 'Your earlier search for "%s" found no real match.\n' % query
        query = v.get("next_query") or query
    return {"query": query, "hits": [], "matched_issue": matched, "rounds": MAX_SEARCH_ROUNDS}


CLAIM_CHECKER = """A code submission claims to do something. Check whether the code
actually supports that claim.

What it says it does:
%(claim)s

The change it makes:
%(patch)s

The current contents of the main file it touches, from the project as it stands:
%(source)s

Do not take the description on trust. Judge only from the code.

Reply as JSON:
{"supported": true or false or "cannot tell",
 "why": "one or two sentences pointing at what in the code decided it",
 "touches_real_code": true or false}"""


def fetch_source(path, sha, cache):
    """WE fetch the file, not the model. It stays blind."""
    key = (path, sha)
    if key in cache:
        return cache[key]
    try:
        r = subprocess.run(
            ["gh", "api", "repos/microsoft/vscode/contents/%s?ref=%s" % (path, sha),
             "--jq", ".content"], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            cache[key] = None
            return None
        cache[key] = base64.b64decode(r.stdout.strip()).decode("utf-8", "replace")
        return cache[key]
    except Exception:
        cache[key] = None
        return None


def check_claims(ci, sha, cache, trace):
    files = ci.get("changed_files") or []
    target = next((f for f in files if f.endswith((".ts", ".js", ".py", ".json"))), None)
    source = fetch_source(target, sha, cache) if target else None
    if not source:
        trace.append({"role": "claim_checker", "action": "no source available",
                      "file": target, "result": "skipped"})
        return {"supported": "cannot tell", "why": "source not retrievable",
                "file": target}
    env = call(CLAIM_CHECKER % {
        "claim": (ci.get("title") or "") + "\n" + (ci.get("body") or "")[:900],
        "patch": (ci.get("patch") or "")[:9000],
        "source": source[:14000]}, "claim_checker")
    out = parse(env.get("result", ""), {"supported": "cannot tell"})
    out["file"] = target
    trace.append({"role": "claim_checker", "action": "read the real source and judged",
                  "file": target, "source_chars": len(source),
                  "supported": out.get("supported"), "why": out.get("why"),
                  "cost": env.get("total_cost_usd")})
    return out


ADJUDICATOR = """%(spec)s

Submission title: %(title)s

Description:
%(body)s

Files changed (%(nfiles)d):
%(files)s

The change:
%(patch)s

--- what the investigator found ---
It searched for: "%(query)s"
Problems it turned up: %(listing)s
Its judgement: %(matched)s

--- what the claim checker found, after reading the real source ---
Claim supported by the code: %(supported)s
Reason: %(why)s
%(feedback)s
Decide the pile. Cite only what you can point at.
"""

REWORK = """
--- YOUR PREVIOUS ANSWER DID NOT HOLD UP ---
You said: pile %(bucket)s, citing %(cites)s
Problem: %(failure)s
Reconsider with that in mind. If the evidence no longer supports your pile,
change it.
"""


def adjudicate(ci, found, claims, feedback, trace, attempt):
    listing = ", ".join("#%d" % h["number"] for h in found["hits"][:8]) or "none"
    files = "\n".join("  " + p for p in (ci.get("changed_files") or [])[:25]) or "  (none)"
    env = call(ADJUDICATOR % {
        "spec": task_spec.BUCKET_DEFINITIONS + "\n" + task_spec.OUTPUT_CONTRACT,
        "title": ci.get("title"), "body": (ci.get("body") or "(none)")[:1500],
        "nfiles": len(ci.get("changed_files") or []), "files": files,
        "patch": (ci.get("patch") or "")[:9000], "query": found["query"],
        "listing": listing, "matched": found.get("matched_issue") or "no genuine match",
        "supported": claims.get("supported"), "why": claims.get("why") or "n/a",
        "feedback": feedback}, "adjudicator")
    v = parse(env.get("result", ""), {"bucket": 0, "citations": [],
                                      "reason": "unparseable", "confidence": "low"})
    v["bucket"] = int(v.get("bucket", 0) or 0)
    v.setdefault("citations", [])
    trace.append({"role": "adjudicator", "action": "decided the pile", "attempt": attempt,
                  "bucket": v["bucket"], "citations": v["citations"],
                  "reason": v.get("reason"), "cost": env.get("total_cost_usd")})
    return v


def verify(v, ci, known, trace):
    """Checks every claim. Returns a failure string when something does not hold
    up, which SENDS THE WORK BACK rather than deleting it quietly."""
    own = set(ci.get("changed_files") or [])
    bad = []
    for c in v.get("citations") or []:
        c = str(c).strip()
        m = re.fullmatch(r"#(\d+)", c)
        if m:
            if int(m.group(1)) not in known:
                bad.append(c + " is not a real recorded problem in this project")
        elif c not in own:
            bad.append(c + " is not among the files this submission changes")
    if v.get("bucket") == 1 and not any(str(c).startswith("#")
                                        for c in v.get("citations") or []):
        bad.append("pile 1 means it fixes an already-reported problem, but no "
                   "problem number was cited")
    trace.append({"role": "verifier", "action": "checked every claim",
                  "claims": v.get("citations"), "failures": bad,
                  "sending_back": bool(bad)})
    return "; ".join(bad) if bad else None


def run_case(case, search, known, sha, cache):
    ci = case["input"]
    trace = []
    found = investigate(ci, search, trace)
    claims = check_claims(ci, sha, cache, trace)
    feedback, verdict = "", None
    for attempt in range(1, MAX_REVISIONS + 2):
        verdict = adjudicate(ci, found, claims, feedback, trace, attempt)
        failure = verify(verdict, ci, known, trace)
        if not failure or attempt > MAX_REVISIONS:
            if failure:
                verdict["unresolved"] = failure
            break
        feedback = REWORK % {"bucket": verdict["bucket"],
                             "cites": verdict.get("citations"), "failure": failure}
    verdict["_trace"] = trace
    verdict["_investigator_rounds"] = found["rounds"]
    verdict["_claim_supported"] = claims.get("supported")
    verdict["_cost"] = round(sum(s.get("cost") or 0 for s in trace), 4)
    return verdict


def generate():
    os.makedirs(RESPONSE_DIR, exist_ok=True)
    os.makedirs(SCRATCH, exist_ok=True)
    search, known = IssueSearch(), scoring.known_issue_numbers()
    sha = json.load(open("data/manifest.json"))["pinned_commit_sha"]
    cache = {}
    for case in scoring.load_cases():
        n = case["input"]["number"]
        path = "%s/pr-%d.json" % (RESPONSE_DIR, n)
        if os.path.exists(path):
            print("  pr-%d: cached" % n)
            continue
        t0 = time.time()
        v = run_case(case, search, known, sha, cache)
        v["_wall_seconds"] = round(time.time() - t0, 1)
        json.dump(v, open(path, "w"), indent=2)
        back = sum(1 for s in v["_trace"] if s.get("sending_back"))
        print("  pr-%d: pile %s (truth %s), %d search round(s), %d sent back, %.3f usd"
              % (n, v["bucket"], case["truth"]["bucket"],
                 v["_investigator_rounds"], back, v["_cost"]))


def replay():
    cases = scoring.load_cases()
    truth = {c["input"]["number"]: c["truth"]["bucket"] for c in cases}
    by_num = {c["input"]["number"]: c["input"] for c in cases}
    pred, cites, cost = {}, {}, 0.0
    rounds = back = checked = 0
    missing = []
    for c in cases:
        n = c["input"]["number"]
        p = "%s/pr-%d.json" % (RESPONSE_DIR, n)
        if not os.path.exists(p):
            missing.append(n)
            continue
        v = json.load(open(p))
        pred[n] = v["bucket"]
        cites[n] = v.get("citations") or []
        cost += v.get("_cost") or 0
        rounds += v.get("_investigator_rounds") or 1
        back += sum(1 for s in v.get("_trace") or [] if s.get("sending_back"))
        if v.get("_claim_supported") not in (None, "cannot tell"):
            checked += 1
    if missing:
        print("missing: %s" % missing, file=sys.stderr)
        return {}
    res = scoring.report("the agent: investigate, check, decide, verify",
                         pred, cites, truth, by_num)
    print("searches decided  : %d rounds across %d cases (%d follow-up searches "
          "the agent chose itself)" % (rounds, len(pred), rounds - len(pred)))
    print("claims tested     : %d/%d against the real source" % (checked, len(pred)))
    print("sent back to redo : %d" % back)
    print("measured cost     : %.4f usd" % cost)
    res.update({"cost_usd": round(cost, 4), "search_rounds": rounds,
                "claims_checked": checked, "sent_back": back})
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
        json.dump(out, open("data/results_agent.json", "w"), indent=2)
