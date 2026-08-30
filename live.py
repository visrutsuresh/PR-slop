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
from itertools import zip_longest
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
import memory
import retriever
import task_spec

OUT_DIR = "reports"

# Measured, not guessed: the recorded five-submission run took 145 seconds,
# which is 29 each. An earlier estimate used 25 and ran about 16% optimistic.
SECONDS_EACH = 29

# Above this many submissions the tool quotes the bill and waits. A judge who
# clones this and types the obvious command should not discover the price
# afterwards.
CONFIRM_ABOVE = int(os.environ.get("PRSLOP_CONFIRM_ABOVE", "12"))

# Off switch for the GitHub-search half of the investigator's retrieval, so the
# same queue can be run both ways in one sitting. The open queue changes every
# day, so a before/after taken hours apart compares two different queues.
GH_SEARCH_ON = os.environ.get("PRSLOP_GH_SEARCH", "1") != "0"


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


def gh_search(repo, words, k):
    """GitHub's issue search, scoped to one repository, issues only."""
    out = subprocess.run(
        ["gh", "api", "-X", "GET", "search/issues",
         "--field", f"q=repo:{repo} is:issue {words}",
         "--field", f"per_page={k}"],
        capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError((out.stderr or "")[:200])
    return json.loads(out.stdout).get("items") or []


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

    def __init__(self, repo, rows, cache, mem=None):
        self.repo = repo
        self.corpus = {r["number"]: ("open" if r.get("state") == "open"
                                     else "closed") for r in rows}
        self.cache = cache
        self.mem = mem
        self.recalled = 0

    def classify(self, n, repo=None):
        repo = repo or self.repo
        if repo.lower() == self.repo.lower() and n in self.corpus:
            return self.corpus[n]
        # Whether an issue exists and is open is a fact about the repository,
        # not about this run, so a previous run's answer is still good. This is
        # the only thing memory is allowed to skip a network call for.
        if self.mem is not None:
            hit = memory.cached_issue(self.mem, repo, n)
            if hit:
                self.recalled += 1
                return hit
        got = resolve_issue(repo, n, self.cache)
        if self.mem is not None:
            memory.remember_issue(self.mem, repo, n, got)
        return got

    def __contains__(self, n):
        return self.classify(n) in ("open", "closed")


def depth_options(repo, open_count=None, each=0.45):
    """The choices worth offering, with the bill attached to each.

    A bare number means nothing to someone who has not priced a run. "100" is
    45 USD and forty minutes; "5" is pocket change and two. Offering the
    options with their cost turns an invisible decision into a visible one.

    Returned as data so both surfaces can use it: the terminal prompts with it,
    and the MCP tool hands it to the assistant to put in front of the person.
    """
    opts = [(5, "a quick look, enough to see the shape of the queue"),
            (25, "a morning's reading"),
            (100, "the default depth, where the piles and the caps start to matter")]
    if open_count:
        opts.append((open_count, "every open submission in the repository"))
    out = []
    for n, why in opts:
        if open_count and n > open_count and n != open_count:
            continue
        out.append({"n": n, "why": why, "usd": round(n * each, 2),
                    "minutes": round(n * SECONDS_EACH / 60)})
    return out


def format_options(repo, opts, open_count=None):
    lines = [f"How much of {repo} should be read?"]
    if open_count:
        lines.append(f"{open_count} pull requests are open right now.")
    lines.append("")
    for o in opts:
        lines.append(f'  {o["n"]:>5}   about {o["usd"]:>6.2f} USD, '
                     f'{o["minutes"]:>3} min   {o["why"]}')
    lines.append("")
    lines.append("  whats_new is free and offline, and on most days it is the "
                 "right first question.")
    return "\n".join(lines)


def ask_depth(repo, opts, open_count=None):
    """Prompt on a terminal. Returns a count, or None if there is nobody to ask."""
    if not sys.stdin.isatty():
        return None
    print(format_options(repo, opts, open_count), file=sys.stderr)
    default = 25
    try:
        raw = input(f"How many? [{default}] ").strip()
    except (EOFError, KeyboardInterrupt):
        print("", file=sys.stderr)
        return 0
    if not raw:
        return default
    if raw.lower() in ("n", "no", "q", "quit", "cancel"):
        return 0
    try:
        return max(1, int(raw))
    except ValueError:
        print("[live] not a number, nothing was run.", file=sys.stderr)
        return 0


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
    # 5 pages of 50 caps a bounded fetch at 250. A whole-queue scan passes a
    # huge limit, so the page ceiling has to lift with it or "all" quietly
    # means "the first 250".
    max_page = 200 if limit > 250 else 5
    while len(out) < limit and page <= max_page:
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
            "additions": sum(f.get("additions") or 0 for f in files),
            "file_adds": {f["filename"]: (f.get("additions") or 0) for f in files}}


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
        "test_lines": sum(v for k, v in (ci.get("file_adds") or {}).items()
                          if TEST_PATH.search(k)),
        "files": len(ci["changed_files"]),
        "lines": ci["additions"],
        "claim": verdict.get("_claim_supported"),
    }


class UnionSearch(LiveSearch):
    """Local index first, then ask GitHub, and give GitHub reserved slots.

    The local index only ever held the 300 most recently filed problems. For a
    repository like this one that is about 300 numbers out of roughly 333,000,
    so anything reported more than a few days ago was unreachable at ANY model
    quality. Two of the three declarations in the recorded run, #231076 and
    #330410, sat outside that window.

    GitHub's own search covers the whole history. We union the two rather than
    replacing, because the local index still wins on recent problems whose
    wording is close, and because a search outage must not leave the
    investigator with nothing.

    Reserved slots matter: taking the top 8 of the merged list would let 8 good
    local hits crowd GitHub out entirely, which is the exact case this exists
    to fix. So the merge alternates, local, remote, local, remote.

    The result shape is identical to the local one, so no prompt changes.
    """

    def __init__(self, rows, repo):
        super().__init__(rows)
        self.repo = repo
        self.searched = 0
        self.failed = 0
        self.narrowed = 0

    def _narrow(self, query, n=3):
        """The 3 rarest words in the query, by the local index's own idf.

        GitHub search ANDs its terms; the local matcher soft-ORs them. So the
        one query the investigator wrote for a soft-OR matcher returns nothing
        from GitHub as soon as it is more than a few words long. Measured:
        "memory leak extension host pseudoterminal" returns 0, while
        "terminal memory leak" returns the plausible issue.

        Dropping to the rarest terms is a retry, not a rewrite, and it uses the
        idf table we already built. No model call, no prompt change.
        """
        toks = [w for w in dict.fromkeys(re.findall(r"[A-Za-z0-9_]{3,}", query))]
        toks.sort(key=lambda w: -self.idf.get(w.lower(), 0.0))
        return " ".join(toks[:n])

    def _remote(self, query, k):
        if not GH_SEARCH_ON:
            return []
        # ponytail: one page, one narrowing retry. Upgrade path: page it if a
        # real query ever needs more than k hits from GitHub.
        words = " ".join(re.findall(r"[A-Za-z0-9_]{3,}", query)[:12])
        if not words:
            return []
        raw = []
        for attempt, q in enumerate((words, self._narrow(query))):
            if not q:
                continue
            try:
                self.searched += 1
                raw = gh_search(self.repo, q, k)
            except Exception as e:
                self.failed += 1
                print(f"    [search] GitHub search unavailable, local index only "
                      f"({type(e).__name__})", file=sys.stderr)
                return []
            if raw:
                if attempt:
                    self.narrowed += 1
                break
        # a pull request is not a reported problem
        return [{"number": it["number"], "title": it.get("title") or "",
                 "score": None, "source": "remote",
                 "excerpt": ((it.get("body") or "").strip()[:300])}
                for it in raw if "pull_request" not in it]

    def _local(self, query, k):
        hits = super().search(query, k)
        for h in hits:
            h["source"] = "local"
        return hits

    def search(self, query, k=8):
        local = self._local(query, k)
        remote = self._remote(query, k)
        out, seen = [], set()
        for a, b in zip_longest(local, remote):
            for h in (a, b):
                if h and h["number"] not in seen:
                    seen.add(h["number"])
                    out.append(h)
        return out[:k]


def run(repo, limit, include_drafts, only=None, review=None, scan_all=False):
    # Pointed at ONE submission, the maintainer's question is "is this any
    # good", not "which pile". Review defaults on there and off for a scan,
    # because it is a per-submission model call a queue should not pay for.
    if review is None:
        review = bool(only)
    if only:
        print(f"[live] fetching pull request #{only} from {repo}")
        prs = fetch_one(repo, only)
    elif scan_all:
        prs = fetch_open_prs(repo, 10 ** 9, include_drafts)
        print(f"[live] scanning the WHOLE queue: {len(prs)} open pull requests")
    else:
        print(f"[live] fetching open pull requests from {repo}")
        prs = fetch_open_prs(repo, limit, include_drafts)
    if not prs:
        print("no open pull requests found", file=sys.stderr)
        return None
    print(f"[live] {len(prs)} open. fetching recorded problems to search")
    corpus = fetch_issue_corpus(repo)
    print(f"[live] {len(corpus)} recorded problems")
    search = UnionSearch(corpus, repo)
    mem = memory.load(repo)
    known = ResolvedIssues(repo, corpus, {}, mem)
    sha = json.loads(gh(f"repos/{repo}/commits?per_page=1"))[0]["sha"]
    os.makedirs(A.SCRATCH, exist_ok=True)

    results, cache = [], {}
    for pr in prs:
        ci = build_input(pr, repo)
        declared = declared_refs(pr, repo, known)
        print(f"  #{ci['number']} {ci['title'][:52]}", flush=True)
        trace = []
        found = A.investigate(ci, search, trace)
        claims = A.check_claims(ci, sha, cache, trace, repo)
        v = A.adjudicate(ci, found, claims, "", trace, 1)
        failure = A.verify(v, ci, known, trace)
        if failure:
            v = A.adjudicate(ci, found, claims,
                             A.REWORK % {"bucket": v["bucket"],
                                         "cites": v.get("citations"),
                                         "failure": failure}, trace, 2)
            A.verify(v, ci, known, trace)
        v["_claim_supported"] = claims.get("supported")
        rev = review_one(ci, sha, cache, repo, trace) if review else None
        v["_cost"] = round(sum(s.get("cost") or 0 for s in trace), 4)
        results.append({"pr": pr, "input": ci, "verdict": v, "review": rev,
                        "facts": facts_for(ci, v, known, declared),
                        "cost": v["_cost"],
                        "searches": found["rounds"]})
    rank(results)
    # rank() first, so `today` is settled before memory records whether we ever
    # put this submission in front of the maintainer.
    prior_runs = mem.get("runs") or 0
    memory.annotate(mem, results)
    saved = memory.save(mem)
    if known.recalled:
        print(f"[live] {known.recalled} issue lookups answered from memory, "
              f"not re-fetched", file=sys.stderr)
    if not saved:
        print("[live] could not write the memory store, this run is not "
              "remembered", file=sys.stderr)
    return {"repo": repo, "sha": sha, "corpus": len(corpus),
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "prior_runs": prior_runs,
            "recalled_lookups": known.recalled,
            "results": results}


REVIEWER = """A maintainer is deciding what to do with this submission. They have already
been told which pile it falls in and what evidence supports it. What they do NOT
have is a read on the WORK ITSELF.

Judge the change on its merits. You are not predicting whether it was merged and
you are not guessing at anyone's intentions. You are answering: if I merged this
tomorrow, what am I taking on?

Title: %(title)s

Description:
%(body)s

Files changed (%(nfiles)d): %(files)s
Added lines: %(adds)d, of which %(testadds)d are in test files.

The change:
%(patch)s

%(source)s

Ground the whole answer in what you can point at in the diff. If you cannot see
something, say you cannot see it rather than assuming it is absent. A missing
test you looked for is a finding; a missing test you inferred is noise.

Reply as JSON:
{"quality": "solid" | "workable" | "needs work" | "cannot tell",
 "headline": "one sentence a maintainer could paste into a review comment",
 "strengths": ["what this genuinely does well, each pointing at the code"],
 "improvements": [{"what": "the concrete change to ask for",
                   "why": "what goes wrong without it",
                   "where": "file or function, or null if it is repo-wide"}],
 "blocking": ["anything that should stop a merge outright, empty list if none"],
 "risk": "what breaks if this is wrong, one sentence"}"""


def review_one(ci, sha, cache, repo, trace):
    """The second question a maintainer asks, which triage never answered.

    Triage says WHICH pile. It never says whether the code is any good, and on a
    single submission that is the whole question. This runs only when the tool is
    pointed at one pull request, because it is a per-submission cost that a queue
    scan should not pay.

    It deliberately does not see the bucket, the evidence chips or the
    investigator's search. Handing it our own conclusion invites it to agree with
    us, and a reviewer that agrees with the thing it is checking is worthless.
    """
    files = ci.get("changed_files") or []
    fa = ci.get("file_adds") or {}
    target = A.pick_claim_file(files, fa)
    src = A.fetch_source(target, sha, cache, repo) if target else None
    env = A.call(REVIEWER % {
        "title": ci.get("title"), "body": (ci.get("body") or "(none)")[:2000],
        "nfiles": len(files),
        "files": ", ".join(files[:20]) + (" ..." if len(files) > 20 else ""),
        "adds": ci.get("additions") or 0,
        "testadds": sum(v for k, v in fa.items() if TEST_PATH.search(k)),
        "patch": (ci.get("patch") or "")[:12000],
        "source": (f"The current contents of {target}, as the project stands:\n"
                   + src[:12000]) if src else
                  "(the main file could not be retrieved, judge from the diff alone)",
    }, "adjudicator")
    out = A.parse(env.get("result", ""), {"quality": "cannot tell",
                                          "headline": "", "strengths": [],
                                          "improvements": [], "blocking": [],
                                          "risk": ""})
    out["_cost"] = env.get("total_cost_usd") or 0
    trace.append({"role": "reviewer", "action": "judged the work itself",
                  "file": target, "quality": out.get("quality"),
                  "improvements": len(out.get("improvements") or []),
                  "cost": out["_cost"]})
    return out


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
    # 100 is the default queue depth: enough that the piles and the today-caps
    # mean something, where 8 was a demo. It is also about 45 USD, which is why
    # anything past CONFIRM_ABOVE quotes the bill before it spends it.
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--drafts", action="store_true", help="include drafts")
    ap.add_argument("--pr", type=int, help="triage one specific pull request")
    ap.add_argument("--all", action="store_true",
                    help="scan EVERY open pull request, not just --limit")
    ap.add_argument("--review", action="store_true",
                    help="also judge code quality and what to improve "
                         "(default ON for --pr, OFF for a queue scan)")
    ap.add_argument("--no-review", action="store_true",
                    help="skip the quality review even on a single pull request")
    ap.add_argument("--yes", action="store_true",
                    help="do not stop for the cost estimate on a large scan")
    a = ap.parse_args()
    t0 = time.time()
    rev = None
    if a.review:
        rev = True
    if a.no_review:
        rev = False
    if not a.pr and not a.yes:
        each = 0.45 + (0.25 if rev else 0)
        n = a.limit
        open_count = None
        if a.all:
            open_count = len(fetch_open_prs(a.repo, 10 ** 9, a.drafts))
            n = open_count
        if n > CONFIRM_ABOVE:
            opts = depth_options(a.repo, open_count, each)
            chosen = ask_depth(a.repo, opts, open_count)
            if chosen is None:
                # No terminal to ask. Print the menu and spend nothing, so a
                # script or a CI job never discovers the price afterwards.
                print(format_options(a.repo, opts, open_count), file=sys.stderr)
                print(f"\n[live] Nothing has been spent. Re-run with --limit N, "
                      f"or --yes to accept {n} at about {n * each:.0f} USD.",
                      file=sys.stderr)
                raise SystemExit(2)
            if not chosen:
                raise SystemExit(0)
            a.limit, a.all = chosen, (open_count is not None and chosen >= open_count)
    data = run(a.repo, a.limit, a.drafts, a.pr, rev, a.all)
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
