#!/usr/bin/env python3
"""Harvest the PR-slop evaluation set from microsoft/vscode.

Gated by contrarian plan-review PASS loop 3 (change_id prslop-harvest-2026-08-29,
Meta/receipts/contrarian-2026-08-29-2230-prslop-harvest-planreview-loop3.md),
conditions A-G. Cites: PRD.md sections 6, 7.0-7.2, 8, 9, 13.

ponytail: fetch-and-write script, not a framework. No classes beyond what
the stdlib already gives us. Idempotent: a second run with no flags is a
no-op once data/cases/ + data/manifest.json exist; --force redoes it all.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_OWNER = "microsoft"
REPO_NAME = "vscode"
REPO = f"{REPO_OWNER}/{REPO_NAME}"

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
CASES_DIR = DATA_DIR / "cases"
ISSUES_PATH = DATA_DIR / "issues.jsonl"
MANIFEST_PATH = DATA_DIR / "manifest.json"
SALT_PATH = DATA_DIR / "pseudonym_salt.txt"

PSEUDONYM_SALT = "micro1-vscode-triage-2026"
REDACT_TOKEN = "[REDACTED-CLOSING-REF]"

# Frozen by contrarian loop-3 condition C. Verified against 11 crafted forms
# plus 100 live PRs. Do not rewrite it: it defines the label AND does the
# strip, so the two can never diverge.
CLOSING_RE = re.compile(
    r'\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s*:?\s*'
    r'(?:https://github\.com/(?P<u_owner>[\w.-]+)/(?P<u_repo>[\w.-]+)/issues/(?P<u_num>\d+)'
    r'|(?:(?P<s_owner>[\w.-]+)/(?P<s_repo>[\w.-]+))?\#(?P<h_num>\d+))\b', re.I)

# Condition A: created_at excluded (AUC 86.2% leak on the true window).
# Condition D: changed_files/patch are NOT on raw_pr as returned by the
# API; the caller must overwrite these two keys with the corrected sources
# (files-list endpoint, patch_url) before build_input() is called.
ALLOWED = ("number", "title", "body", "changed_files", "patch")

BOT_LOGINS = {"vscodebot-pr", "vs-code-engineering", "dependabot[bot]"}
OUTSIDER_ASSOCIATIONS = {"CONTRIBUTOR", "FIRST_TIME_CONTRIBUTOR", "NONE"}

PR_POOL_SIZE = 500          # raw fetch depth, deduped, source for both census and sampling
CENSUS_WINDOW = 100         # section 7.0 / condition E: the true most-recently-closed window
ISSUE_RECENT_N = 200        # corpus part 1 target count of real (non-PR) issues
DISTRACTOR_BAND = 25        # corpus part 3: +/- N around each seeded target
CASES_PER_BUCKET = 5
BUCKET3_MIN_OUTSIDERS = 3


# --------------------------------------------------------------------------
# gh CLI wrappers. AUTH per task brief: call GitHub via subprocess + gh api,
# never touch a token file directly.
# --------------------------------------------------------------------------

def _gh(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], capture_output=True, text=True)


def _gh_json(path: str) -> Any:
    proc = _gh(["api", path])
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {path} failed: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def _gh_json_or_none(path: str) -> Any:
    proc = _gh(["api", path])
    if proc.returncode != 0:
        return None
    return json.loads(proc.stdout)


def _gh_text(url: str) -> str:
    proc = _gh(["api", url])
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {url} failed: {proc.stderr.strip()}")
    return proc.stdout


def gh_version() -> str:
    proc = _gh(["--version"])
    return proc.stdout.splitlines()[0] if proc.stdout else "unknown"


# --------------------------------------------------------------------------
# The frozen closing-reference pattern: matching, labelling, redaction.
# --------------------------------------------------------------------------

def _closing_matches(text: str) -> list[dict]:
    matches = []
    for m in CLOSING_RE.finditer(text or ""):
        if m.group("u_num"):
            owner, repo, num, form = m.group("u_owner"), m.group("u_repo"), m.group("u_num"), "url"
        else:
            owner = m.group("s_owner") or REPO_OWNER
            repo = m.group("s_repo") or REPO_NAME
            num = m.group("h_num")
            form = "shorthand" if m.group("s_owner") else "bare"
        in_repo = owner.lower() == REPO_OWNER.lower() and repo.lower() == REPO_NAME.lower()
        matches.append({"owner": owner, "repo": repo, "number": int(num), "form": form, "in_repo": in_repo})
    return matches


def pr_matches(raw_pr: dict) -> list[dict]:
    text = (raw_pr.get("title") or "") + "\n" + (raw_pr.get("body") or "")
    return _closing_matches(text)


def assign_bucket(raw_pr: dict) -> tuple[int, list[dict]]:
    """Bucket 1: merged AND an in-repo declared closing reference (condition B).
    Bucket 2: merged, no in-repo declared reference (an out-of-repo one does
    not count, per condition B's carve-out). Bucket 3: closed, not merged."""
    matches = pr_matches(raw_pr)
    if raw_pr.get("merged_at") is None:
        return 3, matches
    return (1 if any(m["in_repo"] for m in matches) else 2), matches


def build_input(raw_pr: dict) -> dict:
    """ALLOW-LIST, not a deny-list (7.1.1). Copies exactly the five allowed
    fields into a fresh dict; never deletes from the source. `raw_pr` must
    already carry the corrected `changed_files` (file-path list) and
    `patch` (diff text) values before this is called."""
    out = {k: raw_pr[k] for k in ALLOWED}
    out["title"] = CLOSING_RE.sub(REDACT_TOKEN, out["title"] or "")
    out["body"] = CLOSING_RE.sub(REDACT_TOKEN, out["body"] or "")
    out["patch"] = scrub_patch(out["patch"] or "")
    return out


IDENTITY_LINE_RE = re.compile(r"^(From|Date|Co-authored-by|Signed-off-by):.*$", re.M | re.I)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")
IDENTITY_TOKEN = "[REDACTED-IDENTITY]"


def scrub_patch(patch: str) -> str:
    """Remove contributor identity and any surviving closing reference from the
    diff text.

    Two defects made this necessary, both measured on the shipped 15 cases:
    every patch carried a `From:` line with a real name and mail address (15 of
    15), falsifying the README's claim that the system never sees who submitted
    a pull request and leaving a no-model identity shortcut worth 53.3% balanced
    accuracy against a 33.3% floor; and one patch (case 308696) still contained
    `Fixes #305306`, the exact declaration the strip exists to remove.

    Publishing real personal mail addresses would also breach ground rules 6
    and 8. The scrub is deterministic so it can be applied to already-committed
    cases without re-running the harvest, which matters because the closed-pull
    window has moved and a re-run would produce a different case set."""
    patch = IDENTITY_LINE_RE.sub(IDENTITY_TOKEN, patch)
    patch = EMAIL_RE.sub(IDENTITY_TOKEN, patch)
    patch = CLOSING_RE.sub(REDACT_TOKEN, patch)
    return patch


def pseudonym(login: str) -> str:
    digest = hashlib.sha256((login + PSEUDONYM_SALT).encode()).hexdigest()[:8]
    return f"AUTHOR-{digest}"


def is_bot(raw_pr: dict) -> bool:
    user = raw_pr.get("user") or {}
    login = (user.get("login") or "").lower()
    return user.get("type") == "Bot" or login.endswith("[bot]") or login in BOT_LOGINS


def is_outside_contributor(raw_pr: dict) -> bool:
    return raw_pr.get("author_association") in OUTSIDER_ASSOCIATIONS


# --------------------------------------------------------------------------
# Fetchers
# --------------------------------------------------------------------------

def fetch_closed_pr_pool(pool_size: int = PR_POOL_SIZE) -> list[dict]:
    prs, seen, page = [], set(), 1
    while len(prs) < pool_size:
        batch = _gh_json(
            f"repos/{REPO}/pulls?state=closed&sort=updated&direction=desc"
            f"&per_page=100&page={page}"
        )
        if not batch:
            break
        for pr in batch:
            if pr["number"] not in seen:
                seen.add(pr["number"])
                prs.append(pr)
        page += 1
        if page > 10:
            break
    prs = [pr for pr in prs if pr.get("closed_at")]
    prs.sort(key=lambda pr: pr["closed_at"], reverse=True)
    return prs[:pool_size]


def fetch_files(number: int) -> list[str]:
    files: list[str] = []
    for page in (1, 2, 3):
        batch = _gh_json(f"repos/{REPO}/pulls/{number}/files?per_page=100&page={page}")
        files.extend(f["filename"] for f in batch)
        if len(batch) < 100:
            break
    return files


def fetch_patch(patch_url: str) -> str:
    return _gh_text(patch_url)


def fetch_recent_issues(target_n: int = ISSUE_RECENT_N) -> list[dict]:
    issues, page = [], 1
    while len(issues) < target_n and page <= 20:
        batch = _gh_json(f"repos/{REPO}/issues?state=all&sort=updated&direction=desc&per_page=100&page={page}")
        if not batch:
            break
        issues.extend(item for item in batch if "pull_request" not in item)
        page += 1
    return issues[:target_n]


def fetch_issue_by_number(number: int) -> dict | None:
    if number <= 0:
        return None
    return _gh_json_or_none(f"repos/{REPO}/issues/{number}")


def fetch_commit_before(iso_ts: str) -> str:
    batch = _gh_json(f"repos/{REPO}/commits?until={iso_ts}&per_page=1")
    if not batch:
        raise RuntimeError(f"no commit found before {iso_ts}")
    return batch[0]["sha"]


# --------------------------------------------------------------------------
# Sampling
# --------------------------------------------------------------------------

def _finalize(candidates: list[dict], target_n: int, exclude: set[int] | None = None) -> list[tuple[dict, list[str], str]]:
    """Fetch files+patch for candidates in recency order, keep the first
    target_n whose body AND patch are both non-empty (7.0 sampling rule)."""
    exclude = exclude or set()
    finalized: list[tuple[dict, list[str], str]] = []
    for pr in candidates:
        if len(finalized) >= target_n:
            break
        if pr["number"] in exclude:
            continue
        if not (pr.get("body") or "").strip():
            continue
        files = fetch_files(pr["number"])
        patch = fetch_patch(pr["patch_url"])
        if not patch.strip():
            continue
        finalized.append((pr, files, patch))
    return finalized


def select_bucket_1_or_2(candidates: list[dict], target_n: int = CASES_PER_BUCKET):
    return _finalize(candidates, target_n)


def select_bucket_3(candidates: list[dict], target_n: int = CASES_PER_BUCKET,
                     min_outsiders: int = BUCKET3_MIN_OUTSIDERS):
    """7.0.2: at least `min_outsiders` of the final `target_n` must be
    non-bot outside-contributor closes. Take those first (most recent),
    then fill the remainder from the full remaining pool by recency."""
    outsiders = [pr for pr in candidates if is_outside_contributor(pr) and not is_bot(pr)]
    picked = _finalize(outsiders, min_outsiders)
    used = {pr["number"] for pr, _, _ in picked}
    remaining_needed = target_n - len(picked)
    if remaining_needed > 0:
        picked.extend(_finalize(candidates, remaining_needed, exclude=used))
    picked.sort(key=lambda t: t[0]["closed_at"], reverse=True)
    return picked


def ensure_positive_control(selected: dict[int, list[tuple[dict, list[str], str]]],
                             matches_by_number: dict[int, list[dict]],
                             pool_by_bucket: dict[int, list[dict]]) -> None:
    """Test requirement 6: at least one of the 15 must have caught a URL or
    shorthand form specifically, not just bare #N. If the initial recency
    pick has none, swap the least-recent bucket-1 case for the most-recent
    bucket-1 candidate carrying a url/shorthand form."""
    all_numbers = [pr["number"] for cases in selected.values() for pr, _, _ in cases]
    forms_seen = {m["form"] for n in all_numbers for m in matches_by_number[n]}
    if "url" in forms_seen or "shorthand" in forms_seen:
        return
    used = set(all_numbers)
    for pr in pool_by_bucket[1]:
        if pr["number"] in used:
            continue
        forms = {m["form"] for m in matches_by_number[pr["number"]]}
        if "url" in forms or "shorthand" in forms:
            candidate = _finalize([pr], 1)
            if candidate:
                selected[1][-1] = candidate[0]
                selected[1].sort(key=lambda t: t[0]["closed_at"], reverse=True)
                return
    print("[harvest] WARNING: could not find a url/shorthand closing form for the positive control", file=sys.stderr)


# --------------------------------------------------------------------------
# Corpus
# --------------------------------------------------------------------------

def _trim_issue(issue: dict) -> dict:
    return {
        "number": issue["number"],
        "title": issue.get("title"),
        "body": issue.get("body"),
        "state": issue.get("state"),
        "created_at": issue.get("created_at"),
        "closed_at": issue.get("closed_at"),
        "labels": [lbl.get("name") for lbl in (issue.get("labels") or []) if isinstance(lbl, dict)],
        "html_url": issue.get("html_url"),
    }


def build_corpus(chosen_numbers: list[int], matches_by_number: dict[int, list[dict]]):
    corpus: dict[int, dict] = {}
    for issue in fetch_recent_issues():
        corpus[issue["number"]] = _trim_issue(issue)
    recent_n_count = len(corpus)

    seed_targets: set[int] = set()
    out_of_repo: list[dict] = []
    for case_number in chosen_numbers:
        for m in matches_by_number[case_number]:
            if m["in_repo"]:
                seed_targets.add(m["number"])
            else:
                out_of_repo.append({"case": case_number, "owner": m["owner"],
                                     "repo": m["repo"], "number": m["number"]})

    for t in sorted(seed_targets):
        if t not in corpus:
            issue = fetch_issue_by_number(t)
            if issue and "pull_request" not in issue:
                corpus[t] = _trim_issue(issue)

    for t in sorted(seed_targets):
        for n in range(t - DISTRACTOR_BAND, t + DISTRACTOR_BAND + 1):
            if n in corpus or n <= 0:
                continue
            issue = fetch_issue_by_number(n)
            if issue and "pull_request" not in issue:
                corpus[n] = _trim_issue(issue)

    return corpus, sorted(seed_targets), out_of_repo, recent_n_count


def verify_corpus(seed_targets: list[int], corpus: dict[int, dict]) -> list[int]:
    return [t for t in seed_targets if t not in corpus]


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

def _already_harvested() -> bool:
    if not (CASES_DIR.exists() and MANIFEST_PATH.exists()):
        return False
    return len(list(CASES_DIR.glob("pr-*.json"))) == 15


def harvest(force: bool = False) -> int:
    if not force and _already_harvested():
        print("[harvest] 15 cases + manifest already present, skipping (use --force to redo)")
        return 0

    if force:
        for f in CASES_DIR.glob("pr-*.json"):
            f.unlink()
        if ISSUES_PATH.exists():
            ISSUES_PATH.unlink()

    CASES_DIR.mkdir(parents=True, exist_ok=True)

    print("[harvest] fetching closed PR pool...")
    pool = fetch_closed_pr_pool()
    print(f"[harvest] pool: {len(pool)} closed PRs, deduped")

    matches_by_number: dict[int, list[dict]] = {}
    bucket_by_number: dict[int, int] = {}
    for pr in pool:
        bucket, matches = assign_bucket(pr)
        bucket_by_number[pr["number"]] = bucket
        matches_by_number[pr["number"]] = matches

    census_pool = pool[:CENSUS_WINDOW]
    census = {1: 0, 2: 0, 3: 0}
    for pr in census_pool:
        census[bucket_by_number[pr["number"]]] += 1
    closed_at_min = min(pr["closed_at"] for pr in census_pool)
    closed_at_max = max(pr["closed_at"] for pr in census_pool)
    window_days = (
        datetime.fromisoformat(closed_at_max.replace("Z", "+00:00"))
        - datetime.fromisoformat(closed_at_min.replace("Z", "+00:00"))
    ).total_seconds() / 86400
    print(f"[harvest] re-derived census (top {CENSUS_WINDOW}, frozen pattern): "
          f"{census[1]}/{census[2]}/{census[3]}")

    pool_by_bucket = {1: [], 2: [], 3: []}
    for pr in pool:
        pool_by_bucket[bucket_by_number[pr["number"]]].append(pr)

    # Same window as census_re_derived (top CENSUS_WINDOW), not the wider
    # 500-PR sampling reservoir, so this sums to exactly census[3] and is
    # directly comparable to the published census figure.
    bucket3_population = {"bot": 0, "insider": 0, "outsider": 0}
    for pr in census_pool:
        if bucket_by_number[pr["number"]] != 3:
            continue
        if is_bot(pr):
            bucket3_population["bot"] += 1
        elif is_outside_contributor(pr):
            bucket3_population["outsider"] += 1
        else:
            bucket3_population["insider"] += 1

    print("[harvest] sampling 5/5/5...")
    selected = {
        1: select_bucket_1_or_2(pool_by_bucket[1]),
        2: select_bucket_1_or_2(pool_by_bucket[2]),
        3: select_bucket_3(pool_by_bucket[3]),
    }
    for bucket, cases in selected.items():
        if len(cases) < CASES_PER_BUCKET:
            print(f"[harvest] BLOCKED: only found {len(cases)}/{CASES_PER_BUCKET} usable "
                  f"cases for bucket {bucket} (non-empty body+patch"
                  + (", >=3 outsiders" if bucket == 3 else "") + " required)", file=sys.stderr)
            return 1

    ensure_positive_control(selected, matches_by_number, pool_by_bucket)

    bucket3_selected = {"bot": 0, "insider": 0, "outsider": 0}
    for pr, _, _ in selected[3]:
        if is_bot(pr):
            bucket3_selected["bot"] += 1
        elif is_outside_contributor(pr):
            bucket3_selected["outsider"] += 1
        else:
            bucket3_selected["insider"] += 1

    print("[harvest] writing cases...")
    chosen_numbers: list[int] = []
    case_numbers_by_bucket: dict[int, list[int]] = {1: [], 2: [], 3: []}
    for bucket, cases in selected.items():
        for pr, files, patch in cases:
            enriched = dict(pr)
            enriched["changed_files"] = files
            enriched["patch"] = patch
            case_input = build_input(enriched)
            matches = matches_by_number[pr["number"]]
            truth = {
                "number": pr["number"],
                "bucket": bucket,
                "merged": bucket != 3,
                "closed_at": pr.get("closed_at"),
                "created_at": pr.get("created_at"),
                "author_pseudonym": pseudonym(pr["user"]["login"]),
                "author_association": pr.get("author_association"),
                "is_bot": is_bot(pr),
                "link_declared": any(m["in_repo"] for m in matches),
                "closing_ref_forms": sorted({m["form"] for m in matches}),
                "referenced_issues": [
                    {"owner": m["owner"], "repo": m["repo"], "number": m["number"], "in_repo": m["in_repo"]}
                    for m in matches
                ],
            }
            case = {"input": case_input, "truth": truth}
            (CASES_DIR / f"pr-{pr['number']}.json").write_text(json.dumps(case, indent=2) + "\n")
            chosen_numbers.append(pr["number"])
            case_numbers_by_bucket[bucket].append(pr["number"])

    print("[harvest] building issue corpus...")
    corpus, seed_targets, out_of_repo, recent_n_count = build_corpus(chosen_numbers, matches_by_number)
    with ISSUES_PATH.open("w") as f:
        for number in sorted(corpus):
            f.write(json.dumps(corpus[number]) + "\n")
    print(f"[harvest] corpus: {len(corpus)} issues "
          f"({recent_n_count} recent-N, {len(seed_targets)} seeded targets, "
          f"{len(out_of_repo)} out-of-repo excluded)")

    print("[harvest] verifying every seeded reference resolves...")
    missing = verify_corpus(seed_targets, corpus)
    if missing:
        print(f"[harvest] BLOCKED: {len(missing)} in-repo referenced issue(s) "
              f"unresolved against the frozen corpus: {missing}", file=sys.stderr)
        return 1

    print("[harvest] pinning source-read commit (condition F)...")
    pinned_sha = fetch_commit_before(closed_at_min)

    SALT_PATH.write_text(PSEUDONYM_SALT + "\n")

    manifest = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repo": REPO,
        "gh_version": gh_version(),
        "queries": {
            "closed_pr_pool": {
                "endpoint": f"repos/{REPO}/pulls",
                "params": {"state": "closed", "sort": "updated", "direction": "desc", "per_page": 100},
                "pages_fetched": min(10, (len(pool) + 99) // 100) if pool else 0,
                "deduped_count": len(pool),
            },
            "census_window": {
                "size": CENSUS_WINDOW,
                "closed_at_min": closed_at_min,
                "closed_at_max": closed_at_max,
                "window_days": round(window_days, 4),
            },
            "pr_files": f"repos/{REPO}/pulls/{{number}}/files?per_page=100",
            "pr_patch": "{patch_url}",
            "issues_recent": {
                "endpoint": f"repos/{REPO}/issues",
                "params": {"state": "all", "sort": "updated", "direction": "desc", "per_page": 100},
                "target_n": ISSUE_RECENT_N,
                "actual_n": recent_n_count,
            },
            "issue_by_number": f"repos/{REPO}/issues/{{number}}",
            "distractor_band": {"width": DISTRACTOR_BAND, "seeded_targets": len(seed_targets)},
            "commit_pin": f"repos/{REPO}/commits?until={{closed_at_min}}&per_page=1",
        },
        "census_re_derived": {
            "bucket_1": census[1], "bucket_2": census[2], "bucket_3": census[3],
            "pool_size": CENSUS_WINDOW, "window_days": round(window_days, 4),
            "note": "re-derived under the frozen CLOSING_RE pattern (condition E), "
                    "not the earlier 15/74/11 count in PRD 7.0",
        },
        "case_counts": {str(b): len(case_numbers_by_bucket[b]) for b in (1, 2, 3)},
        "case_numbers": {str(b): sorted(case_numbers_by_bucket[b]) for b in (1, 2, 3)},
        "bucket_3_composition": {"selected": bucket3_selected, "population_pool_100": bucket3_population},
        "issue_corpus_count": len(corpus),
        "issue_corpus_recent_n": recent_n_count,
        "issue_corpus_seeded_targets": seed_targets,
        "pinned_commit_sha": pinned_sha,
        "pinned_commit_predates": closed_at_min,
        "out_of_repo_references": out_of_repo,
        "verification": {
            "in_repo_targets": len(seed_targets),
            "resolved": len(seed_targets) - len(missing),
            "unresolved": len(missing),
            "excluded_out_of_repo": len(out_of_repo),
        },
        "pseudonym_salt_file": str(SALT_PATH.relative_to(ROOT)),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    print("[harvest] done. manifest written to", MANIFEST_PATH)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="redo the harvest even if 15 cases already exist")
    args = parser.parse_args()
    return harvest(force=args.force)


if __name__ == "__main__":
    sys.exit(main())
