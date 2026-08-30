#!/usr/bin/env python3
"""Point it at any repository. It triages the pull requests actually waiting.

Everything else in this project runs on 15 CLOSED submissions, because closed
ones are the only place answers exist to score against. That made it an
evaluation, not a tool. A maintainer's queue is OPEN pull requests, and there
are no answers there, which is the whole reason they need help.

This runs the same four roles on the real open queue and writes a page they
open in a browser.

    python3 live.py microsoft/vscode --limit 8

There is nothing to score here and we do not pretend otherwise. What it gives
you is checked evidence per submission and a suggested order.
"""
import argparse
import base64
import html
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

import agent_v4 as A
import retriever
import task_spec

OUT_DIR = "reports"


def gh(path, jq=None):
    cmd = ["gh", "api", path]
    if jq:
        cmd += ["--jq", jq]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[:300])
    return r.stdout


def fetch_one(repo, number):
    """Point it at one specific open pull request. A reviewer working a queue by
    hand wants this far more often than they want the whole list."""
    pr = json.loads(gh(f"repos/{repo}/pulls/{number}"))
    if pr.get("state") != "open":
        print(f"note: #{number} is {pr.get('state')}, not open. Triaging anyway.",
              file=sys.stderr)
    return [pr]


def fetch_open_prs(repo, limit, include_drafts=False):
    out = []
    page = 1
    while len(out) < limit and page <= 5:
        batch = json.loads(gh(f"repos/{repo}/pulls?state=open&sort=created"
                              f"&direction=desc&per_page=50&page={page}"))
        if not batch:
            break
        for p in batch:
            if p.get("draft") and not include_drafts:
                continue
            out.append(p)
            if len(out) >= limit:
                break
        page += 1
    return out


def fetch_issue_corpus(repo, count=300):
    """The recorded problems the investigator searches. Pull requests share the
    same number counter as issues on GitHub, so they must be filtered out."""
    rows, page = [], 1
    while len(rows) < count and page <= 6:
        batch = json.loads(gh(f"repos/{repo}/issues?state=all&sort=created"
                              f"&direction=desc&per_page=100&page={page}"))
        if not batch:
            break
        for it in batch:
            if "pull_request" in it:
                continue
            rows.append({"number": it["number"], "title": it.get("title") or "",
                         "body": (it.get("body") or "")[:4000],
                         "state": it.get("state")})
        page += 1
    return rows[:count]


def build_input(pr, repo):
    """Same allow-list as the evaluation: five fields, identity scrubbed. A real
    maintainer would see who filed it, but we keep the tool blind to that on
    purpose, because judging the person is not what this is for."""
    files = json.loads(gh(f"repos/{repo}/pulls/{pr['number']}/files?per_page=100"))
    paths = [f["filename"] for f in files]
    patch = "\n".join(f"--- {f['filename']}\n{f.get('patch') or ''}"
                      for f in files)[:40000]
    from harvest import scrub_patch
    return {"number": pr["number"],
            "title": scrub_patch(pr.get("title") or ""),
            "body": scrub_patch((pr.get("body") or "")[:8000]),
            "changed_files": paths,
            "patch": scrub_patch(patch)}


class LiveSearch(retriever.IssueSearch):
    def __init__(self, rows):
        from collections import Counter
        import math
        self.issues = rows
        self.docs, df = [], Counter()
        for iss in self.issues:
            c = Counter(retriever.tokenise(f"{iss['title']} {iss['body']}"[:4000]))
            self.docs.append(c)
            df.update(c.keys())
        n = max(len(self.docs), 1)
        self.idf = {w: math.log(1 + n / (1 + c)) for w, c in df.items()}


TEST_PATH = re.compile(r"(^|/)(test|tests|spec|__tests__)/|\.(test|spec)\.[tj]s$", re.I)


def facts_for(ci, verdict, known):
    cites = [str(c).strip() for c in (verdict.get("citations") or [])]
    issue_cites = [c for c in cites if c.startswith("#")]
    return {
        "problems": [c for c in issue_cites if int(c[1:]) in known],
        "invented": [c for c in issue_cites if int(c[1:]) not in known],
        "has_tests": any(TEST_PATH.search(f) for f in ci["changed_files"]),
        "files": len(ci["changed_files"]),
        "lines": len(re.findall(r"^\+(?!\+\+)", ci["patch"] or "", re.M)),
        "claim": verdict.get("_claim_supported"),
    }


def run(repo, limit, include_drafts, only=None):
    if only:
        print(f"[live] fetching pull request #{only} from {repo}")
        prs = fetch_one(repo, only)
    else:
        print(f"[live] fetching open pull requests from {repo}")
        prs = fetch_open_prs(repo, limit, include_drafts)
    if not prs:
        print("no open pull requests found", file=sys.stderr)
        return None
    print(f"[live] {len(prs)} open. fetching recorded problems to search")
    corpus = fetch_issue_corpus(repo)
    print(f"[live] {len(corpus)} recorded problems")
    search = LiveSearch(corpus)
    known = {i["number"] for i in corpus}
    sha = json.loads(gh(f"repos/{repo}/commits?per_page=1"))[0]["sha"]
    os.makedirs(A.SCRATCH, exist_ok=True)

    results, cache = [], {}
    for pr in prs:
        ci = build_input(pr, repo)
        print(f"  #{ci['number']} {ci['title'][:52]}", flush=True)
        trace = []
        found = A.investigate(ci, search, trace)
        claims = A.check_claims(ci, sha, cache, trace)
        v = A.adjudicate(ci, found, claims, "", trace, 1)
        failure = A.verify(v, ci, known, trace)
        if failure:
            v = A.adjudicate(ci, found, claims,
                             A.REWORK % {"bucket": v["bucket"],
                                         "cites": v.get("citations"),
                                         "failure": failure}, trace, 2)
            A.verify(v, ci, known, trace)
        v["_claim_supported"] = claims.get("supported")
        v["_cost"] = round(sum(s.get("cost") or 0 for s in trace), 4)
        results.append({"pr": pr, "input": ci, "verdict": v,
                        "facts": facts_for(ci, v, known),
                        "cost": v["_cost"],
                        "searches": found["rounds"]})
    rank(results)
    return {"repo": repo, "sha": sha, "corpus": len(corpus),
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "results": results}


def rank(results):
    """Order within each pile, and mark how many are worth doing today.

    The decider judges each submission on its own, so with a large queue a pile
    can hold sixty items, which is the original problem again. Two things fix
    that, and neither is a model change.

    Ordering: by how much CHECKED evidence supports it. A confirmed link to a
    reported problem outranks a confirmed description, which outranks tests,
    which outranks size. Size is last on purpose, because a big diff is work,
    not value.

    A cap: only the strongest few in each pile are marked as today's reading.
    The rest stay visible and stay ordered. Nothing is hidden, because a hidden
    submission is one nobody ever looks at again.
    """
    CAP = {1: 5, 2: 8, 3: 99, 0: 99}
    for bucket in (1, 2, 3, 0):
        grp = [r for r in results if (r["verdict"].get("bucket") or 0) == bucket]
        grp.sort(key=lambda r: (
            -len(r["facts"]["problems"]),
            -(1 if r["facts"]["claim"] is True else 0),
            -(1 if r["facts"]["has_tests"] else 0),
            -r["facts"]["lines"],
        ))
        for i, r in enumerate(grp):
            r["rank"] = i + 1
            r["today"] = i < CAP.get(bucket, 99)
        for r in grp:
            r["group_size"] = len(grp)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", help="owner/name, e.g. microsoft/vscode")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--drafts", action="store_true", help="include drafts")
    ap.add_argument("--pr", type=int, help="triage one specific pull request")
    a = ap.parse_args()
    t0 = time.time()
    data = run(a.repo, a.limit, a.drafts, a.pr)
    if not data:
        raise SystemExit(1)
    os.makedirs(OUT_DIR, exist_ok=True)
    slug = a.repo.replace("/", "-") + (f"-pr{a.pr}" if a.pr else "")
    json.dump(data, open(f"{OUT_DIR}/{slug}.json", "w"), indent=2, default=str)
    import report
    path = report.write(data, f"{OUT_DIR}/{slug}.html")
    total = sum(r["cost"] for r in data["results"])
    print(f"\n[live] {len(data['results'])} triaged in {time.time()-t0:.0f}s, "
          f"{total:.2f} usd")
    print(f"[live] open this: {os.path.abspath(path)}")
