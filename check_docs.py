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


if __name__ == "__main__":
    sys.exit(main())
