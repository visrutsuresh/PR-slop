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


def gh_status(path):
    """Same call as gh(), but hands back the HTTP status instead of raising.

    The resolver has to tell "there is no such issue" (404, a genuine
    invention) apart from "we could not look" (403 rate limit, network,
    timeout). gh() raises RuntimeError and throws the status away, and calling
    a real issue invented is the exact harm the resolver exists to remove, so
    this path never guesses: anything it cannot read a 404 out of is a
    non-answer.
    """
    try:
        r = subprocess.run(["gh", "api", path], capture_output=True, text=True,
                           timeout=60)
    except (subprocess.SubprocessError, OSError) as e:
        return None, "", str(e)[:300]
    if r.returncode == 0:
        return 0, r.stdout, ""
    m = re.search(r"\(HTTP (\d+)\)", r.stderr)
    return (int(m.group(1)) if m else None), "", r.stderr[:300]


def resolve_issue(repo, n, cache):
    """One lookup per (repo, number) for the whole run.

    open | closed | pull_request | missing | unresolved. "missing" is reserved
    for a 404. Everything else we could not check says so instead.
    """
    key = (repo.lower(), n)
    if key not in cache:
        code, out, err = gh_status(f"repos/{repo}/issues/{n}")
        if code == 0:
            try:
                payload = json.loads(out)
            except json.JSONDecodeError:
                payload = {}
            cache[key] = ("pull_request" if "pull_request" in payload
                          else "open" if payload.get("state") == "open"
                          else "closed")
        elif code == 404:
            cache[key] = "missing"
        else:
            cache[key] = "unresolved"
        # ponytail: one stderr line per lookup, not a structured log. Enough
        # to tell a rate limit apart from a bug during a run. Upgrade path: if
        # this ever needs machine reading, write the same dict into the report
        # JSON alongside the facts.
        note = f"  [{err.strip()}]" if cache[key] == "unresolved" else ""
        print(f"[live]   ref {repo}#{n} -> {cache[key]}{note}", file=sys.stderr)
    return cache[key]


class ResolvedIssues:
    """Membership for agent_v4.verify(): the corpus window first, then one live
    GitHub lookup, cached.

    verify() touches this in exactly one way, `int(...) not in known`
    (agent_v4.py:316), so a __contains__ object drops in with agent_v4.py
    unedited. The evaluation path builds its own plain set, so no published
    number can move.

    A real issue is in, whatever its state, which stops the rework loop
    deleting a correct citation to an issue that merely sits below the corpus
    window. A pull request number, a 404 and a lookup we could not finish are
    all out: a rework prompt is cheaper than a chip calling a real issue fake.
    """

    def __init__(self, repo, rows, cache):
        self.repo = repo
        self.corpus = {r["number"]: ("open" if r.get("state") == "open"
                                     else "closed") for r in rows}
        self.cache = cache

    def classify(self, n, repo=None):
        repo = repo or self.repo
        if repo.lower() == self.repo.lower() and n in self.corpus:
            return self.corpus[n]
        return resolve_issue(repo, n, self.cache)

    def __contains__(self, n):
        return self.classify(n) in ("open", "closed")


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


def scrub_identity(text):
    """Identity only. The live path keeps the author's closing reference.

    The evaluation also strips that reference, because on a CLOSED submission
    the declaration IS the answer key and leaving it in would let the agent
    read the label off its own input. An open queue has no answer to protect,
    so the same field is the author's own evidence and it stays. Contributor
    names and mail addresses go in both. harvest.scrub_patch and CLOSING_RE are
    untouched.
    """
    from harvest import EMAIL_RE, IDENTITY_LINE_RE, IDENTITY_TOKEN
    return EMAIL_RE.sub(IDENTITY_TOKEN, IDENTITY_LINE_RE.sub(IDENTITY_TOKEN, text))


def fetch_pr_files(repo, number):
    """Paginated, mirroring harvest.fetch_files. One unpaginated page silently
    caps both the file list and the added-line count above 100 changed files."""
    files = []
    # ponytail: three pages, 300 files, mirroring harvest.fetch_files rather
    # than generalising. Upgrade path: loop until a short batch if a real
    # submission ever exceeds it.
    for page in (1, 2, 3):
        batch = json.loads(gh(f"repos/{repo}/pulls/{number}/files"
                              f"?per_page=100&page={page}"))
        files.extend(batch)
        if len(batch) < 100:
            break
    return files


def build_input(pr, repo):
    """The allow-list: five fields the roles read, identity scrubbed. A real
    maintainer would see who filed it, but we keep the tool blind to that on
    purpose, because judging the person is not what this is for.

    `additions` rides along for the report only. It is GitHub's own per-file
    count, because counting "+" lines in a patch capped at 40000 characters
    undercounts every large submission. It never reaches a prompt: the roles
    read title, body, changed_files and patch by name.
    """
    files = fetch_pr_files(repo, pr["number"])
    paths = [f["filename"] for f in files]
    patch = "\n".join(f"--- {f['filename']}\n{f.get('patch') or ''}"
                      for f in files)[:40000]
    return {"number": pr["number"],
            "title": scrub_identity(pr.get("title") or ""),
            "body": scrub_identity((pr.get("body") or "")[:8000]),
            "changed_files": paths,
            "patch": scrub_identity(patch),
            "additions": sum(f.get("additions") or 0 for f in files)}


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


CITE_RE = re.compile(r"#(\d+)")


def quote_for(m, raw):
    """The author's own words around a match, so the chip quotes rather than
    paraphrases.

    The pattern proves a text match and nothing about intent, so "This does not
    fix #123" has to reach the reader as written. Anchoring on the line start
    keeps a markdown marker visible ("- [ ]", ">"), which a fixed lookback
    would cut in half. The matched text is always rendered in full and only the
    prefix is capped: truncating the match would drop the issue number off a
    chip that then says "confirmed".
    """
    start = raw.rfind("\n", 0, m.start()) + 1
    lead = ""
    if m.start() - start <= 40:
        prefix = raw[start:m.start()]
    else:
        prefix, lead = raw[m.start() - 24:m.start()], "\u2026"
        cut = prefix.find(" ")
        if cut != -1:
            prefix = prefix[cut + 1:]
    if len(prefix) > 60:
        prefix, lead = prefix[-60:], "\u2026"
    return (lead + prefix + m.group(0)).strip()


def declared_refs(pr, repo, resolver):
    """Closing references the AUTHOR wrote, read out of the raw title and body
    with harvest's frozen CLOSING_RE.

    Deliberately not harvest.pr_matches(): for a bare #N that falls back to the
    module constants microsoft/vscode, which mis-attributes every bare
    reference on any other repository. live.py is repo-generic, so the fallback
    here is the repository we were pointed at.

    Read from the RAW pull request rather than from build_input's output, so it
    does not depend on what the scrub did or did not remove.
    """
    from harvest import CLOSING_RE
    home_owner, home_name = repo.split("/", 1)
    raw = (pr.get("title") or "") + "\n" + (pr.get("body") or "")
    out, seen = [], set()
    for m in CLOSING_RE.finditer(raw):
        if raw.count("```", 0, m.start()) % 2 == 1:
            continue        # inside a fenced block: an example, not a declaration
        if m.group("u_num"):
            owner = m.group("u_owner")
            name = m.group("u_repo")
            num = int(m.group("u_num"))
        else:
            owner = m.group("s_owner") or home_owner
            name = m.group("s_repo") or home_name
            num = int(m.group("h_num"))
        key = (owner.lower(), name.lower(), num)
        if key in seen:
            continue        # title and body usually repeat it. Say it once.
        seen.add(key)
        out.append({"owner": owner, "repo": name, "number": num,
                    "same_repo": f"{owner}/{name}".lower() == repo.lower(),
                    "quote": quote_for(m, raw),
                    "status": resolver.classify(num, f"{owner}/{name}")})
    return out


def facts_for(ci, verdict, resolver, declared):
    by = {"open": [], "closed": [], "pull_request": [], "missing": [],
          "unresolved": []}
    for c in (verdict.get("citations") or []):
        c = str(c).strip()
        # agent_v4.py:314 parses a citation this way. int(c[1:]) does not, and
        # "#333395 (memory tool)" is a shape the model really returns, so the
        # unguarded parse dies after the whole run has already been paid for.
        m = CITE_RE.fullmatch(c)
        if m:
            by[resolver.classify(int(m.group(1)))].append(c)
    return {
        "problems": by["open"],
        "closed_refs": by["closed"],
        "pr_refs": by["pull_request"],
        "invented": by["missing"],
        "unresolved": by["unresolved"],
        "declared": declared,
        "declared_ok": any(d["status"] == "open" for d in declared),
        "has_tests": any(TEST_PATH.search(f) for f in ci["changed_files"]),
        "files": len(ci["changed_files"]),
        "lines": ci["additions"],
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
    known = ResolvedIssues(repo, corpus, {})
    sha = json.loads(gh(f"repos/{repo}/commits?per_page=1"))[0]["sha"]
    os.makedirs(A.SCRATCH, exist_ok=True)

    results, cache = [], {}
    for pr in prs:
        ci = build_input(pr, repo)
        declared = declared_refs(pr, repo, known)
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
                        "facts": facts_for(ci, v, known, declared),
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

    Ordering, by how much CHECKED evidence supports it:
      1. the author's own text declares a reference that resolves to an open
         issue, pulled out of the title and body with no model involved
      2. a confirmed link to an already-reported problem
      3. a confirmed description
      4. the newer submission first, which is a deterministic RECENCY
         tiebreak and is not evidence of anything

    Tests and size are not in the key and are display-only. Nearly every
    submission has tests, so that key sorted on noise, and size never earns a
    place: a large diff is work, not value, and ranking by it rewards the exact
    thing this tool exists to filter.

    A cap: only the strongest few in each pile are marked as today's reading.
    The rest stay visible and stay ordered. Nothing is hidden, because a hidden
    submission is one nobody ever looks at again.
    """
    CAP = {1: 5, 2: 8, 3: 99, 0: 99}
    for bucket in (1, 2, 3, 0):
        grp = [r for r in results if (r["verdict"].get("bucket") or 0) == bucket]
        grp.sort(key=lambda r: (
            -(1 if r["facts"]["declared_ok"] else 0),
            -len(r["facts"]["problems"]),
            -(1 if r["facts"]["claim"] is True else 0),
            -r["input"]["number"],
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
