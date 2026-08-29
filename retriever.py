#!/usr/bin/env python3
"""Stage 1, the retriever: find reported problems that a pull request might be
answering.

This is the piece the simple comparison system cannot have. The project's
reported problems are far too many to paste into a single prompt, so answering
"does this address something someone already reported?" means going and
searching. That search is the whole reason this is a system rather than a
prompt.

Deliberately plain: word overlap with common words weighted down. No embedding
model, no index, no dependency. If a plain search turns out to be the thing
holding the system back, that becomes a measured finding and a reason to
replace it, which is worth more than assuming something clever was needed.
"""
import json
import math
import re
from collections import Counter

ISSUE_FILE = "data/issues.jsonl"

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "of", "to", "in", "for", "on",
    "with", "is", "are", "was", "were", "be", "been", "it", "this", "that",
    "as", "at", "by", "from", "not", "no", "we", "i", "you", "when", "then",
    "there", "should", "would", "can", "do", "does", "did", "have", "has",
    "vscode", "code", "issue", "bug", "fix", "fixes", "pull", "request",
}

TOKEN_RE = re.compile(r"[a-z][a-z0-9_]{2,}")


def tokenise(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall((text or "").lower()) if t not in STOPWORDS]


class IssueSearch:
    def __init__(self, path: str = ISSUE_FILE):
        self.issues = []
        with open(path) as fh:
            for line in fh:
                if line.strip():
                    self.issues.append(json.loads(line))
        self.docs = []
        df = Counter()
        for iss in self.issues:
            toks = tokenise(f"{iss.get('title','')} {iss.get('body','') or ''}"[:4000])
            counts = Counter(toks)
            self.docs.append(counts)
            df.update(counts.keys())
        n = max(len(self.docs), 1)
        # Rare words carry more signal than common ones. Without this, every
        # query matches whichever issue is simply longest.
        self.idf = {w: math.log(1 + n / (1 + c)) for w, c in df.items()}

    def search(self, query: str, k: int = 8) -> list[dict]:
        q = Counter(tokenise(query))
        if not q:
            return []
        scored = []
        for iss, counts in zip(self.issues, self.docs):
            if not counts:
                continue
            overlap = sum(
                self.idf.get(w, 0.0) * min(qc, counts.get(w, 0))
                for w, qc in q.items()
            )
            if overlap <= 0:
                continue
            # Divide by length so a very long issue does not win on volume alone.
            score = overlap / math.sqrt(sum(counts.values()))
            scored.append((score, iss))
        scored.sort(key=lambda x: -x[0])
        return [
            {"number": iss["number"], "title": iss.get("title", ""),
             "score": round(s, 3),
             "excerpt": ((iss.get("body") or "").strip()[:300])}
            for s, iss in scored[:k]
        ]


if __name__ == "__main__":
    import glob
    s = IssueSearch()
    print(f"corpus: {len(s.issues)} reported problems")
    for p in sorted(glob.glob("data/cases/*.json"))[:3]:
        c = json.load(open(p))
        q = f"{c['input']['title']} {(c['input'].get('body') or '')[:600]}"
        hits = s.search(q, k=3)
        print(f"\npr-{c['input']['number']} (truth bucket {c['truth']['bucket']}), "
              f"really references {c['truth'].get('referenced_issues')}")
        for h in hits:
            print(f"   #{h['number']} score {h['score']}  {h['title'][:70]}")
