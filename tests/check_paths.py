#!/usr/bin/env python3
"""Fail if a tracked doc points a reader at a repo-relative path that does
not exist on disk. check_docs.py compares numbers; it reads no path at all,
so a stale path after the restructure would otherwise be invisible. Part of
./run.sh eval.

A loose extractor here is worse than no check: it either fails constantly
(false positives drown the real signal) or passes vacuously (the anti-vacuity
floor below exists to catch exactly that). Rules, all binding:

(a) Scope is the tracked root docs plus docs/* and run.sh. NOT .py files:
    test_live_refs.py uses docs/x.md as a fixture, and the doc-path SWEEP
    (done separately, at restructure time) already covers .py docstrings.
(b) Normalise: strip backticks/**, trailing punctuation, leading ./, and a
    leading git-revision prefix (HEAD: or a hex commit SHA followed by :),
    e.g. `HEAD:traces/INDEX.md` in a `git show` example.
(c) Skip: contains */?/$/% (glob or shell/printf interpolation), starts with
    / or ~ (not repo-relative), or has no known file extension. Requiring a
    known extension (not merely a slash) is what keeps this check from
    drowning in unrelated slash-bearing text; do not loosen it to hit the
    floor below.
(d) Skip anything inside a fenced code block that is not tagged as a shell
    command (bash/sh/shell/console): those fences hold example output or
    prompt text, not a path meant to resolve on disk.
(e) Allow-list, each entry with its reason. Do NOT edit the referring doc to
    satisfy this checker; the doc's own historical or provisional statement
    is the ground truth, not this list.
(f) Anti-vacuity: assert the candidate count clears FLOOR, so a broken
    extractor fails loudly instead of passing on zero real work. If a
    measured run ever lands under FLOOR, lower FLOOR to the measured number
    and say so here — never loosen (c) to reach it.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FLOOR = 100  # 134 measured at plan-review loop 3; 139 measured against the
             # final swept tree. Lower this, with a note, if a future
             # measured run ever lands below it. Never loosen the extractor.

SCOPE = [
    "README.md", "IMPROVEMENT-CHANGELOG.md", "REPRODUCTION.md",
    "SUBMISSION-CHECKLIST.md", "PRE-EXISTING.md", "AGENT-TRAJECTORIES.md",
    "run.sh",
] + sorted(
    str(p.relative_to(ROOT)) for p in (ROOT / "docs").glob("*") if p.is_file()
)

KNOWN_EXT = (".py", ".md", ".html", ".json", ".jsonl", ".sh", ".txt", ".ts",
             ".yml", ".yaml", ".cfg", ".toml", ".csv")
COMMAND_FENCE_TAGS = {"bash", "sh", "shell", "console", "zsh"}

TOKEN_RE = re.compile(r"[A-Za-z0-9_.~%$*?{}=:-]*/[A-Za-z0-9_.~/%$*?{}=:.-]+")
REV_PREFIX_RE = re.compile(r"^(?:HEAD|[0-9a-f]{7,40}):")

ALLOW = {
    # Deliberately absent / deliberately historical. Each carries its reason.
    "harness/compare.py":
        "PRE-EXISTING.md:39 records that this file was planned and never "
        "built; a competition-integrity statement, not drift.",
    "harness/trace.py":
        "PRE-EXISTING.md:11, describing pre-kickoff commit f8be460's actual "
        "tree at that commit, before the restructure existed. Historical.",
    "harness/__init__.py":
        "PRE-EXISTING.md:12, same commit f8be460 provenance record.",
    "docs/reproduction.md":
        "PRE-EXISTING.md:26, describing pre-kickoff commit 6ab12f8's actual "
        "tree at that commit, before REPRODUCTION.md's rename.",
    "reports/microsoft-vscode.json":
        "IMPROVEMENT-CHANGELOG.md:582, narrating the superseded fixture in "
        "the entry about that very bug. reports/* is gitignored; historical "
        "reference, not drift.",
}


def normalise(token):
    token = token.strip("`*").rstrip(".,;:)\"'!?").lstrip("(\"'")
    token = REV_PREFIX_RE.sub("", token)
    if token.startswith("./"):
        token = token[2:]
    return token


def skip_reason(token):
    if any(c in token for c in "*?$%"):
        return "glob-or-interpolation"
    if token.startswith("/") or token.startswith("~"):
        return "absolute"
    if "/" not in token:
        return "no-slash"
    if not token.endswith(KNOWN_EXT):
        return "no-known-extension"
    return None


def fence_tag(line):
    return line.lstrip()[3:].strip().lower()


def iter_candidates(rel):
    path = ROOT / rel
    is_md = rel.endswith(".md")
    in_fence = False
    fence_is_command = True
    for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if is_md and line.lstrip().startswith("```"):
            if not in_fence:
                fence_is_command = fence_tag(line) in COMMAND_FENCE_TAGS
            in_fence = not in_fence
            continue
        if in_fence and not fence_is_command:
            continue
        for raw in TOKEN_RE.findall(line):
            token = normalise(raw)
            reason = skip_reason(token)
            if reason:
                continue
            yield rel, lineno, token


def main():
    candidates = []
    offenders = []
    for rel in SCOPE:
        if not (ROOT / rel).is_file():
            continue
        for rel_, lineno, token in iter_candidates(rel):
            candidates.append((rel_, lineno, token))
            if token in ALLOW:
                continue
            if not (ROOT / token).exists():
                offenders.append((rel_, lineno, token))

    if len(candidates) < FLOOR:
        print(f"ANTI-VACUITY FAIL: only {len(candidates)} candidate paths "
              f"found, floor is {FLOOR}. The extractor is broken, not the "
              f"docs; do not lower this floor without a fresh measurement.")
        return 1

    if offenders:
        print(f"STALE PATH: {len(offenders)} tracked doc reference(s) point "
              f"at a path that does not exist:")
        for rel, lineno, token in sorted(set(offenders)):
            print(f"   {rel}:{lineno} {token}")
        return 1

    print(f"check_paths: {len(candidates)} candidate paths checked "
          f"(floor {FLOOR}), 0 stale, {len(ALLOW)} allow-listed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
