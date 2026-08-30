#!/usr/bin/env python3
"""What the tool remembers between runs.

A maintainer does not triage once. They open the queue on Monday, again on
Wednesday, again on Friday, and most of what they see is what they already
saw. A tool with no memory makes them re-read the same twenty submissions
every time and re-earn the same conclusions, which is the original problem
wearing a different hat.

Three things are worth carrying forward, and nothing else:

  1. WHICH SUBMISSIONS ARE NEW. The single most useful fact on a repeat visit.
     Everything else on the page is noise if you cannot see what changed.

  2. HOW LONG SOMETHING HAS BEEN WAITING, and whether we have said it was
     worth reading before. A submission the tool ranked first three visits ago
     that is still open is a different object from one filed this morning.

  3. RESOLVED ISSUE LOOKUPS. Whether issue #231076 exists and is open is a
     fact about the repository, not about this run. Re-asking GitHub for it on
     every run is a wasted call, and calls are the thing that costs money and
     hits rate limits.

Deliberately NOT remembered: any model output. Buckets, reasons and claim
verdicts are re-derived every run. Caching a judgement would mean a stale
conclusion silently outliving the evidence that produced it, and this project
has spent a lot of effort making sure conclusions are re-checkable. A cached
fact is a saving. A cached judgement is a lie waiting to happen.

The store is a plain JSON file per repository. No database, no schema
migration, no daemon. If it is missing or corrupt the tool runs exactly as it
did before memory existed, because a memory that can break the tool is worse
than no memory.
"""
import json
import os
from datetime import datetime, timezone

MEM_DIR = os.environ.get("PRSLOP_MEMORY_DIR", ".prslop-memory")
VERSION = 1


def _path(repo):
    return os.path.join(MEM_DIR, repo.replace("/", "-") + ".json")


def load(repo):
    """Never raises. A broken store is treated as no store."""
    try:
        with open(_path(repo)) as fh:
            d = json.load(fh)
        if d.get("version") != VERSION:
            return _empty(repo)
        d.setdefault("seen", {})
        d.setdefault("issues", {})
        return d
    except Exception:
        return _empty(repo)


def _empty(repo):
    return {"version": VERSION, "repo": repo, "runs": 0,
            "last_run": None, "seen": {}, "issues": {}}


def cached_issue(mem, repo, number):
    """A resolved issue state, if we already asked. Facts only."""
    return (mem.get("issues") or {}).get(f"{repo}#{number}")


def remember_issue(mem, repo, number, status):
    # `unresolved` means we could not reach GitHub. Never cache that, or one
    # rate-limited run poisons every later run with a fact we never learned.
    if status and status != "unresolved":
        mem.setdefault("issues", {})[f"{repo}#{number}"] = status


def annotate(mem, results, now=None):
    """Add first_seen, times_seen and is_new to each result. Pure, no I/O."""
    now = now or datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d %H:%M UTC")
    seen = mem.setdefault("seen", {})
    for r in results:
        n = str(r["input"]["number"])
        prior = seen.get(n)
        r["is_new"] = prior is None
        r["first_seen"] = (prior or {}).get("first_seen", stamp)
        r["times_seen"] = ((prior or {}).get("times_seen", 0)) + 1
        r["was_today_before"] = bool((prior or {}).get("was_today"))
        seen[n] = {"first_seen": r["first_seen"],
                   "times_seen": r["times_seen"],
                   "last_seen": stamp,
                   "was_today": bool(r.get("today")) or r["was_today_before"]}
    return results


def save(mem, now=None):
    """Never raises. Failing to write memory must not fail the run."""
    now = now or datetime.now(timezone.utc)
    mem["runs"] = (mem.get("runs") or 0) + 1
    mem["last_run"] = now.strftime("%Y-%m-%d %H:%M UTC")
    try:
        os.makedirs(MEM_DIR, exist_ok=True)
        tmp = _path(mem["repo"]) + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(mem, fh, indent=2, sort_keys=True)
        os.replace(tmp, _path(mem["repo"]))   # atomic, no half-written store
        return True
    except Exception:
        return False
