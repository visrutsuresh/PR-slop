#!/usr/bin/env python3
"""Fail if a number published in the docs no longer matches what the code prints.

This exists because it kept happening. The README described the wrong system,
then carried the wrong per-pile figures, then quoted a cost that changed when
one case was regenerated. Every time, the docs drifted and only a human reading
carefully noticed.

Runs offline from the committed cache. Part of ./run.sh eval.
"""
import re
import subprocess
import sys


def live(cmd):
    out = subprocess.run(["./run.sh", cmd], capture_output=True, text=True).stdout
    got = {}
    m = re.search(r"balanced accuracy : ([\d.]+)%\s+per-bucket \[([^\]]+)\]", out)
    if m:
        got["accuracy"] = m.group(1) + "%"
        got["recall"] = " / ".join(x.strip().strip("\'") for x in m.group(2).split(","))
    m = re.search(r"measured cost     : ([\d.]+)", out)
    if m:
        got["cost"] = f"{float(m.group(1)):.2f} USD"
    return got


def main():
    # strip markdown emphasis and collapse whitespace, so "1.00 / **0.20**"
    # still matches the plain "1.00 / 0.20" the code prints
    docs = re.sub(r"[*`]", "", open("README.md").read())
    docs = re.sub(r"\s+", " ", docs)
    problems = []
    for name in ("baseline", "script", "agent"):
        got = live(name)
        for label, value in got.items():
            if value not in docs:
                problems.append(f"{name}: {label} is {value}, not found in README.md")
    if problems:
        print("DOC DRIFT, the README no longer matches what the code prints:")
        for p in problems:
            print("   " + p)
        return 1
    print("docs match the code: accuracy, per-pile recall and cost for all three systems")
    return 0


def check_depth_menu():
    """The published depth menu must be exactly what the code prints.

    Four of its nine lines were once stale, carrying a time estimate the code
    had already corrected, in a file that in the same commit claimed the
    correction was done. Nothing caught it, because this script only ever
    checked accuracy, recall and cost. This exists because it kept happening.
    """
    import live
    real = live.format_options(
        "microsoft/vscode", live.depth_options("microsoft/vscode", 1782), 1782)
    rows = [l.rstrip() for l in real.splitlines() if "about" in l and "USD" in l]
    bad = []
    for path in ("README.md", "CHANGELOG.md"):
        text = open(path).read()
        for row in rows:
            n = row.split()[0]
            published = [l.rstrip() for l in text.splitlines()
                         if l.strip().startswith(n + " ") and "USD" in l]
            for p in published:
                if p != row:
                    bad.append(f"{path}: depth row for {n} is stale\n"
                               f"      published {p.strip()}\n"
                               f"      code says {row.strip()}")
    if bad:
        print("DOC DRIFT, the published depth menu is not what the code prints:")
        for b in bad:
            print("   " + b)
        return False
    return True


if __name__ == "__main__":
    rc = main()
    if not check_depth_menu():
        rc = 1
    sys.exit(rc)
