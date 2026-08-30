#!/usr/bin/env python3
"""The product: one command, one page a maintainer reads on a Monday morning.

Everything else in this repository produces numbers for a judge. This produces
the thing a maintainer would actually open. It is the difference between an
evaluation and a tool.

It never touches anything. It reads, it reports, a human decides.
"""
import json
import glob
import os
import sys

import scoring
from evidence import evidence_for, strength


def clip(text, n):
    """Cut at a word boundary. Cutting mid-word makes a page look unfinished,
    which is exactly the impression a triage report must not give."""
    text = " ".join((text or "").split())
    if len(text) <= n:
        return text
    cut = text[:n].rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:.") + "..."


def short(path):
    """Full paths blow the layout apart. The last two segments are enough to
    recognise a file; the report says where the full path lives."""
    parts = str(path).split("/")
    return "/".join(parts[-2:]) if len(parts) > 2 else str(path)

AGENT_DIR = os.environ.get("PRSLOP_AGENT_DIR", "data/responses/agent-v4")
BAR = "=" * 74


def load(agent_dir):
    known = scoring.known_issue_numbers()
    items = []
    for p in sorted(glob.glob("data/cases/*.json")):
        case = json.load(open(p))
        n = case["input"]["number"]
        rp = f"{agent_dir}/pr-{n}.json"
        if not os.path.exists(rp):
            continue
        v = json.load(open(rp))
        ev = evidence_for(case, v, known)
        items.append({
            "number": n,
            "title": (case["input"].get("title") or "").strip(),
            "bucket": v.get("bucket"),
            "reason": (v.get("reason") or "").strip(),
            "citations": v.get("citations") or [],
            "confidence": v.get("confidence", "unknown"),
            "evidence": ev,
            "strength": strength(ev),
            "closed_unmerged": case["truth"]["bucket"] == 3,
        })
    return items


def facts(ev):
    """Only things that are true or false. No opinions on this line."""
    out = []
    if ev["cites_real_problem"] is True:
        out.append("fixes reported " + ", ".join(ev["problems_cited"]))
    if ev["claim_supported"] is True:
        out.append("code matches its description")
    elif ev["claim_supported"] is False:
        out.append("code does NOT match its description")
    out.append("has tests" if ev["has_tests"] else "no tests")
    out.append(f"{ev['lines_added']} lines, {ev['files_touched']} file(s)")
    return " | ".join(out)


def render_one(item):
    """One submission, for a reviewer working through the queue by hand.

    Real reviewers open things one at a time, so the tool has to support that.
    It is deliberately NOT part of the evaluation: judging a single item in
    isolation is close to what one prompt already does, and scoring it would
    misrepresent where the value is. It is a convenience built on the same
    pipeline, and it says so.
    """
    ev = item["evidence"]
    L = [BAR, f"  #{item['number']}  {clip(item['title'], 56)}", BAR, ""]
    L.append(f"  https://github.com/microsoft/vscode/pull/{item['number']}")
    L.append("")
    L.append("  EVIDENCE, each of these is checkable against the repository")
    L.append(f"    reported problem : {', '.join(ev['problems_cited']) if ev['cites_real_problem'] is True else 'none named'}")
    supported = {True: "yes", False: "NO", None: "could not tell"}.get(ev["claim_supported"], "could not tell")
    L.append(f"    code matches its description : {supported}")
    L.append(f"    tests            : {'yes' if ev['has_tests'] else 'no'}")
    L.append(f"    size             : {ev['lines_added']} lines, {ev['files_touched']} file(s)")
    L.append("")
    L.append(f"  SUGGESTED PILE   : {item['bucket']}  (confidence: {item['confidence']})")
    if item["reason"]:
        L.append(f"  why              : {clip(item['reason'], 200)}")
    if item["closed_unmerged"] and item["strength"] >= 3:
        L += ["", "  NOTE: this was closed without merging, but the evidence above is",
              "  strong. Worth a second look before you move on."]
    L += ["", BAR, "  Nothing was posted, closed, merged or commented on. You decide.", BAR]
    return "\n".join(L)


def render(items):
    lines = []
    add = lines.append

    # A closed submission has no business in an open queue. Earlier this page
    # told the reader to prioritise something and then, further down, that it
    # had already been closed. Closed items appear only in SECOND OPINION.
    live = [i for i in items if not i["closed_unmerged"]]
    ordered = sorted(live, key=lambda i: (i["bucket"] or 9, -i["strength"]))
    now = [i for i in ordered if i["bucket"] == 1]
    soon = [i for i in ordered if i["bucket"] == 2]
    later = [i for i in ordered if i["bucket"] == 3]

    add(BAR)
    add("  PULL REQUEST TRIAGE".ljust(56) + "microsoft/vscode")
    add(BAR)
    add("")
    add(f"  {len(live)} open, {len(items) - len(live)} recently closed.")
    add("  Nothing has been touched. This is a reading list, not an action.")
    add("")

    def block(title, group, note):
        add("-" * 74)
        add(f"  {title}  ({len(group)})")
        add(f"  {note}")
        add("-" * 74)
        if not group:
            add("    nothing here")
            add("")
            return
        for i in group:
            add("")
            add(f"    #{i['number']}  {clip(i['title'], 60)}")
            add(f"      {facts(i['evidence'])}")
            add(f"      https://github.com/microsoft/vscode/pull/{i['number']}")
            if i["reason"]:
                add(f"      why: {clip(i['reason'], 128)}")
            if i["citations"]:
                add(f"      points at: {', '.join(short(c) for c in i['citations'][:3])}")
        add("")

    # An earlier draft printed "roughly N minutes of reading" from a formula
    # invented on the spot. This project already dropped a human-time metric
    # once for being made up, then reintroduced it here. Replaced with counts
    # that are simply true.
    size = sum(i["evidence"]["files_touched"] for i in now)
    ln = sum(i["evidence"]["lines_added"] for i in now)
    block("READ THESE FIRST", now,
          f"Close something already reported. {size} files, {ln} lines added.")
    block("NORMAL QUEUE", soon,
          "Real work. Needs your eyes, no particular urgency.")
    block("LEAVE UNTIL LAST", later,
          "Least supported by evidence. NOT a verdict that they are bad.")

    flagged = [i for i in items if i["closed_unmerged"] and i["strength"] >= 3]
    add(BAR)
    add("  SECOND OPINION")
    add(BAR)
    add("")
    add("  These were closed without merging, but the evidence says they were")
    add("  well supported. Not an accusation. Worth thirty seconds each.")
    add("")
    if not flagged:
        add("    nothing flagged")
    for i in flagged:
        add(f"    #{i['number']}  {clip(i['title'], 60)}")
        add(f"      {facts(i['evidence'])}")
        add(f"      https://github.com/microsoft/vscode/pull/{i['number']}")
        add("")
    add(BAR)
    add("  Every number above resolves against the repository. Nothing was")
    add("  posted, closed, merged or commented on. You decide.")
    add(BAR)
    return "\n".join(lines)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    one = None
    if args and args[0].lstrip("#").isdigit():
        one = int(args.pop(0).lstrip("#"))
    d = args[0] if args else AGENT_DIR
    items = load(d)
    if one is not None:
        hit = next((i for i in items if i["number"] == one), None)
        if not hit:
            print(f"no saved result for #{one}. available: "
                  f"{', '.join(str(i['number']) for i in items)}", file=sys.stderr)
            raise SystemExit(1)
        print(render_one(hit))
        raise SystemExit(0)
    if not items:
        print("no saved responses found", file=sys.stderr)
        raise SystemExit(1)
    report = render(items)
    print(report)
    open("data/triage_report.txt", "w").write(report + "\n")
