"""Reference baseline: what the eval would score if the closing-reference
field had NOT been stripped from `input`.

This is not a competing triage system and it is not meant to be beaten by
a small margin. It exists to measure the LEAK that the harvest step (and
loop-3 conditions B/C) required stripping out. Conditional on `merged`,
the bucket label is a DETERMINISTIC FUNCTION of whether an in-repo closing
reference was declared: bucket 1 = merged + declared, bucket 2 = merged +
not declared. A rule that reads `truth.link_declared` directly therefore
gets buckets 1 and 2 exactly right by construction, which is precisely
the tautology the strip exists to prevent. It never predicts bucket 3
because a declared-or-not signal carries no information about "closed
without merging" at all, so its bucket-3 recall is always zero and its
balanced accuracy is capped near 2/3.

No model, no network. Reads only the committed cache under data/cases/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

CASES_DIR = Path(__file__).resolve().parent.parent / "data" / "cases"


def load_cases() -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(CASES_DIR.glob("pr-*.json"))]


def predict(link_declared: bool) -> int:
    """Declared -> bucket 1, else bucket 2. Bucket 3 is never predicted."""
    return 1 if link_declared else 2


def balanced_accuracy(cases: list[dict]) -> tuple[float, dict[int, float]]:
    correct = {1: 0, 2: 0, 3: 0}
    total = {1: 0, 2: 0, 3: 0}
    for case in cases:
        truth = case["truth"]
        bucket = truth["bucket"]
        total[bucket] += 1
        if predict(truth["link_declared"]) == bucket:
            correct[bucket] += 1
    recalls = {b: (correct[b] / total[b] if total[b] else 0.0) for b in (1, 2, 3)}
    return sum(recalls.values()) / 3, recalls


def main() -> int:
    cases = load_cases()
    if not cases:
        print("no cases found under data/cases/, run harvest.py first", file=sys.stderr)
        return 1
    acc, recalls = balanced_accuracy(cases)
    print(f"cases: {len(cases)}")
    for b in (1, 2, 3):
        print(f"  bucket {b} recall: {recalls[b]:.3f} ({'never predicted' if b == 3 else 'declared-link rule'})")
    print(f"balanced accuracy: {acc:.3f}")
    print()
    print("This measures a leak we found and removed. Pull requests declare")
    print("which problem they fix, and that declaration IS the answer for two")
    print("of the three piles, so a five-line rule with no model scores 67%.")
    print("The harvest step strips that declaration out of what any system")
    print("sees. This number is a reference point, published so the gap is")
    print("visible. It is NOT the baseline our system is compared against;")
    print("that is a single direct prompt, see ./run.sh baseline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
