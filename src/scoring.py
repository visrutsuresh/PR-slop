#!/usr/bin/env python3
"""Scoring, shared by every system so no side gets a different yardstick.

The citation counting rule was fixed IN ADVANCE, before any system was run.
If a system correctly declines to cite because it has no way to check, that is
zero offered, not zero percent correct. Those look very different in a table,
and choosing between them after seeing results would mean picking whichever
flattered us. So three numbers are always reported: how many citations were
offered, how many resolve against the real repository, and a rate stated only
when at least one was offered.
"""
import json
import glob
import re

CASE_GLOB = "data/cases/*.json"
ISSUE_FILE = "data/issues.jsonl"
BUCKETS = (1, 2, 3)


def load_cases() -> list[dict]:
    return [json.load(open(p)) for p in sorted(glob.glob(CASE_GLOB))]


def known_issue_numbers() -> set[int]:
    nums = set()
    with open(ISSUE_FILE) as fh:
        for line in fh:
            if line.strip():
                nums.add(int(json.loads(line)["number"]))
    return nums


def known_file_paths() -> set[str]:
    paths = set()
    for case in load_cases():
        for p in case["input"].get("changed_files") or []:
            paths.add(p)
    return paths


def balanced_accuracy(pred: dict, truth: dict) -> tuple[float, dict]:
    """Mean of the per-bucket recalls. Used instead of plain accuracy because
    the evaluation set is balanced 5/5/5 by design and plain accuracy would
    reward a system that simply favoured whichever bucket is largest."""
    recalls = {}
    for b in BUCKETS:
        members = [n for n, t in truth.items() if t == b]
        hit = sum(1 for n in members if pred.get(n) == b)
        recalls[b] = hit / len(members) if members else 0.0
    return sum(recalls.values()) / len(BUCKETS), recalls


def false_prune_rate(pred: dict, truth: dict) -> tuple[int, int]:
    """The dangerous error: calling something not-merged that the maintainer
    actually merged. Returns (misses, opportunities)."""
    merged = [n for n, t in truth.items() if t in (1, 2)]
    misses = sum(1 for n in merged if pred.get(n) == 3)
    return misses, len(merged)


def citation_audit(citations_by_case: dict, cases_by_number: dict) -> dict:
    """Count citations, separating the ones that were free from the ones that
    required actually checking the project.

    This split was added AFTER the first baseline run produced a misleading
    number. The simple system appeared to score 86.7% on citation validity,
    which looked like it had contradicted our written prediction that a system
    with no repository access would invent references. It had not. Twelve of its
    thirteen 'valid' citations were file paths copied straight out of the case
    it had just been handed. Quoting back a path you were given is not evidence
    of anything, and counting it as such flattered the system.

    Only citations that require looking something up are informative. On those,
    the picture reversed: of three issue numbers offered, two did not exist.

    So three groups are reported:
      self      - a file path that was already in this case's own input, free
      external  - an issue number, which cannot be known without checking
      unknown   - anything else
    The headline rate is computed on EXTERNAL citations only.
    """
    issues = known_issue_numbers()
    self_cited = external_ok = external_bad = unknown = 0
    for number, cites in citations_by_case.items():
        own_paths = set((cases_by_number.get(number, {}).get("changed_files")) or [])
        for c in cites or []:
            c = c.strip()
            m = re.fullmatch(r"#(\d+)", c)
            if m:
                if int(m.group(1)) in issues:
                    external_ok += 1
                else:
                    external_bad += 1
            elif c in own_paths:
                self_cited += 1
            else:
                unknown += 1
    external = external_ok + external_bad
    return {
        "self_cited": self_cited,
        "external_offered": external,
        "external_resolved": external_ok,
        "external_rate": (external_ok / external) if external else None,
        "unknown": unknown,
        "total_offered": self_cited + external + unknown,
    }


def report(name: str, pred: dict, citations: dict, truth: dict,
           cases_by_number: dict) -> dict:
    bal, recalls = balanced_accuracy(pred, truth)
    misses, opps = false_prune_rate(pred, truth)
    cite = citation_audit(citations, cases_by_number)
    abstained = sum(1 for v in pred.values() if v == 0)
    print(f"\n=== {name} ===")
    print(f"balanced accuracy : {bal:.1%}   per-bucket {[f'{recalls[b]:.2f}' for b in BUCKETS]}")
    print(f"false prune       : {misses}/{opps} merged items called not-merged")
    print(f"citations, free   : {cite['self_cited']} file paths copied from the case's own input")
    if cite["external_rate"] is None:
        print(f"citations, real   : 0 offered, so no rate is reportable")
    else:
        print(f"citations, real   : {cite['external_resolved']}/{cite['external_offered']} "
              f"issue numbers exist ({cite['external_rate']:.1%})")
    print(f"declined to call  : {abstained}/{len(pred)}")
    return {"name": name, "balanced_accuracy": bal, "per_bucket_recall": recalls,
            "false_prune": [misses, opps], "citations": cite, "abstained": abstained}
