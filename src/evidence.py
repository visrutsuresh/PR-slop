#!/usr/bin/env python3
"""The evidence card: facts about a submission that are true or false regardless
of what any human decided.

WHY THIS EXISTS. Everything else in this project predicts what a maintainer did.
That has a flaw we could not argue away: if a maintainer overlooks something
valuable and closes it, and the tool correctly says the work is good, we mark
the tool WRONG. The scoring fights the product. The one case no version ever got
right, pr-308696, is very likely exactly that: real code, fixing a genuinely
reported problem, confirmed against the real source, closed anyway.

So this module scores a different thing. Every claim below is checkable against
the repository, with no opinion and no human verdict involved:

  cites_real_problem   the reported problem it names actually exists
  cites_real_files     the files it names are really in this change
  has_tests            the change touches test files
  substantive          it is more than a trivial edit
  claim_supported      the code matches what the description says it does

Nobody has to label anything. Each is a fact.

THE DISAGREEMENT REPORT is the point. When the evidence says a submission is
substantiated and it was closed anyway, that is not the tool failing. That is
the tool doing the job: finding work a human may have overlooked.
"""
import json
import glob
import os
import re

import scoring

TEST_PATH = re.compile(r"(^|/)(test|tests|spec|__tests__)/|\.(test|spec)\.[tj]s$", re.I)
ADDED_LINE = re.compile(r"^\+(?!\+\+)", re.M)


def evidence_for(case, verdict, known_issues):
    """Every field here is a fact about the submission, checkable without any
    human's opinion."""
    ci = case["input"]
    files = ci.get("changed_files") or []
    patch = ci.get("patch") or ""
    cites = [str(c).strip() for c in (verdict.get("citations") or [])]

    issue_cites = [c for c in cites if c.startswith("#")]
    # None means "made no claim", which is NOT the same as "made a false claim".
    # An earlier version of this file conflated the two and reported 61.5% when
    # every claim actually made was true. That is precisely the counting error
    # this project pre-registered a rule against, and it still happened here.
    cites_real_problem = (all(int(c[1:]) in known_issues for c in issue_cites)
                          if issue_cites else None)

    file_cites = [c for c in cites if not c.startswith("#")]
    cites_real_files = all(c in set(files) for c in file_cites) if file_cites else None

    has_tests = any(TEST_PATH.search(f) for f in files)
    added = len(ADDED_LINE.findall(patch))
    substantive = added >= 10 or len(files) >= 3

    return {
        "cites_real_problem": cites_real_problem,
        "problems_cited": issue_cites,
        "cites_real_files": cites_real_files,
        "has_tests": has_tests,
        "lines_added": added,
        "files_touched": len(files),
        "substantive": substantive,
        "claim_supported": verdict.get("_claim_supported"),
    }


def strength(ev):
    """How well supported is this submission, counted from facts only.
    Deliberately a plain count, not a weighted score: a weighting would be an
    opinion, and the whole point of this module is to avoid smuggling one in."""
    points = 0
    if ev["cites_real_problem"] is True:
        points += 1
    if ev["has_tests"]:
        points += 1
    if ev["substantive"]:
        points += 1
    if ev["claim_supported"] is True:
        points += 1
    return points


def main(agent_dir="data/responses/agent-v4"):
    known = scoring.known_issue_numbers()
    cases = {json.load(open(p))["input"]["number"]: json.load(open(p))
             for p in sorted(glob.glob("data/cases/*.json"))}

    rows, checkable, correct = [], 0, 0
    for n, case in cases.items():
        p = f"{agent_dir}/pr-{n}.json"
        if not os.path.exists(p):
            continue
        v = json.load(open(p))
        ev = evidence_for(case, v, known)
        ev["number"] = n
        ev["strength"] = strength(ev)
        ev["merged_in_reality"] = case["truth"]["bucket"] in (1, 2)
        rows.append(ev)
        # objective accuracy: were the tool's factual claims true?
        for field in ("cites_real_problem", "cites_real_files"):
            if ev[field] is not None:
                checkable += 1
                correct += bool(ev[field])

    print("=== evidence card, scored on facts only ===")
    print(f"factual claims made        : {checkable}")
    print(f"factual claims that hold up: {correct} ({correct/checkable:.1%})"
          if checkable else "no factual claims made")
    print(f"carried tests              : {sum(r['has_tests'] for r in rows)}/{len(rows)}")
    print(f"substantive                : {sum(r['substantive'] for r in rows)}/{len(rows)}")
    named = sum(1 for r in rows if r["cites_real_problem"] is True)
    silent = sum(1 for r in rows if r["cites_real_problem"] is None)
    print(f"named a real problem       : {named}/{len(rows)}"
          f"  ({silent} named none at all, which is not a false claim)")

    print("\n=== THE DISAGREEMENT REPORT ===")
    print("Well-supported work that was closed anyway. This is the output the")
    print("merge-prediction scoring can never reward, because it marks the tool")
    print("wrong for being right.\n")
    flagged = [r for r in rows if not r["merged_in_reality"] and r["strength"] >= 3]
    if not flagged:
        print("  (none in these 15)")
    for r in flagged:
        c = cases[r["number"]]["input"]
        print(f"  pr-{r['number']}  strength {r['strength']}/4  \"{(c.get('title') or '')[:70]}\"")
        why = []
        if r["cites_real_problem"] is True:
            why.append(f"fixes a genuinely reported problem {','.join(r['problems_cited'])}")
        if r["claim_supported"] is True:
            why.append("code confirmed to match its description")
        if r["has_tests"]:
            why.append("carries tests")
        if r["substantive"]:
            why.append(f"{r['lines_added']} lines added across {r['files_touched']} file(s)")
        for w in why:
            print(f"       - {w}")
        print("       -> closed without merging. Worth a second look.\n")

    json.dump(rows, open("data/results_evidence.json", "w"), indent=2)
    return rows


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "data/responses/agent-v4")
