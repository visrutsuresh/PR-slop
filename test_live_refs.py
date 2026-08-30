#!/usr/bin/env python3
"""What the author-declared chip is allowed to claim, and nothing more.

The chip says a closing reference APPEARS in the author's own text. It does not
say the author meant it, because a regex cannot know that. So the one thing
that has to hold is that the reader sees the author's words: a negation, an
unticked checkbox or a quote marker must survive into the rendered quote, or
the chip reads as an endorsement of something the author was denying.

Offline. No network, no credential, no model. Part of ./run.sh eval.
"""
import live


class Everything:
    """Stands in for the resolver. These strings are about extraction and
    quoting, so nothing here may depend on an issue really existing."""

    def classify(self, n, repo=None):
        return "open"


def refs(text, repo="microsoft/vscode"):
    return live.declared_refs({"title": text, "body": ""}, repo, Everything())


# (text, what the reader must be able to see in the quote)
QUOTES = [
    ("This does not fix #123", "This does not fix #123"),
    ("It will not close #777 yet", "It will not close #777"),
    ("Do NOT resolve #888", "Do NOT resolve #888"),
    ("- [ ] Fixes #999", "- [ ] Fixes #999"),
    ("> Fixes #4242", "> Fixes #4242"),
    ("I spent a day on this and concluded the change does not fix #123",
     "does not fix #123"),
]


def main():
    checks = 0
    for text, must_contain in QUOTES:
        got = refs(text)
        assert len(got) == 1, (text, got)
        assert must_contain in got[0]["quote"], (text, got[0]["quote"])
        checks += 1

    # the standard pull-request template placeholder is not a declaration
    assert refs("Fixes #<issue number>") == []
    # nor is an example inside a fenced code block
    assert refs("how to use it\n```\nFixes #555\n```\ndone") == []
    checks += 2

    # the number is never truncated off the end of a chip that says "confirmed"
    url = refs("Fixes https://github.com/other/proj/issues/77")
    assert url[0]["quote"].endswith("/issues/77"), url
    assert (url[0]["owner"], url[0]["repo"]) == ("other", "proj"), url
    assert url[0]["same_repo"] is False
    checks += 1

    # a bare #N belongs to the repository we were pointed at, never to vscode
    bare = refs("Fixes #7", repo="acme/widgets")
    assert (bare[0]["owner"], bare[0]["repo"]) == ("acme", "widgets"), bare
    assert bare[0]["same_repo"] is True
    checks += 1

    # title and body repeat the same reference; the card says it once
    both = live.declared_refs({"title": "Fix #231076: restore it",
                               "body": "Fixes #231076 on Windows"},
                              "microsoft/vscode", Everything())
    assert len(both) == 1 and both[0]["quote"] == "Fix #231076", both
    checks += 1

    print(f"declared references: {checks}/{checks} checks passed")
    union_checks()
    eval_path_checks()




class _Stub(live.UnionSearch):
    """Bypasses __init__ so no network or corpus is needed."""
    def __init__(self, local, remote=None, boom=False):
        self.repo, self.searched, self.failed, self.narrowed = "o/r", 0, 0, 0
        self.idf = {}
        self._l, self._r, self._boom = local, remote or [], boom

    def _local(self, q, k):
        return [{"number": n, "title": "l", "score": 1.0, "excerpt": ""} for n in self._l]

    def _remote(self, q, k):
        if self._boom:
            return live.UnionSearch._remote(self, q, k)
        return [{"number": n, "title": "r", "score": None, "excerpt": ""} for n in self._r]


def union_checks():
    checks = 0

    # A plain top-k merge lets 8 good local hits crowd GitHub out entirely,
    # which is the exact failure this exists to fix. The merge must alternate.
    got = [h["number"] for h in _Stub(range(1, 9), (101, 102, 103, 104)).search("q", 8)]
    assert got == [1, 101, 2, 102, 3, 103, 4, 104], got
    assert len([n for n in got if n > 100]) == 4, "remote must keep half the slots"
    checks += 1

    # the same issue found by both sources is shown once
    got = [h["number"] for h in _Stub((5, 6), (5, 7)).search("q", 8)]
    assert got == [5, 6, 7], got
    checks += 1

    # a search outage degrades to local only, and is COUNTED rather than hidden
    orig = live.gh_search
    live.gh_search = lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("rate limited"))
    try:
        st = _Stub([9], boom=True)
        got = [h["number"] for h in st.search("some real words", 8)]
    finally:
        live.gh_search = orig
    assert got == [9], got
    assert st.failed == 1, "a swallowed search failure must still be counted"
    checks += 1

    # GitHub's search returns pull requests alongside issues. A pull request is
    # not a reported problem, and offering one to the investigator as a candidate
    # match is how a submission gets "linked" to another submission.
    orig = live.gh_search
    live.gh_search = lambda repo, words, k: [
        {"number": 11, "title": "a real issue", "body": ""},
        {"number": 12, "title": "actually a pull request", "body": "",
         "pull_request": {"url": "..."}},
    ]
    try:
        got = [h["number"] for h in _Stub([], boom=True).search("some real words", 8)]
    finally:
        live.gh_search = orig
    assert got == [11], got
    checks += 1

    print(f"union search: {checks}/{checks} checks passed")




def eval_path_checks():
    """The published numbers replay from committed JSON and NEVER enter
    check_claims or fetch_source, so `./run.sh agent` returning 73.3% proves
    NOTHING about a change to either. These assert the eval path directly."""
    import agent_v4
    checks = 0

    # the 15 evaluation cases carry no per-file counts, so the chooser must
    # degrade to the original first-match rule and pick the identical file
    files = ["config/barrel.json", "src/big.ts", "src/small.ts", "README.md"]
    assert agent_v4.pick_claim_file(files, None) == "config/barrel.json"
    assert agent_v4.pick_claim_file(files, {}) == "config/barrel.json"
    checks += 2

    # with counts present (live only) it picks the file that gained the most
    assert agent_v4.pick_claim_file(
        files, {"config/barrel.json": 2, "src/big.ts": 400, "src/small.ts": 9}
    ) == "src/big.ts"
    checks += 1

    # ties keep the earlier file, so the choice stays deterministic
    assert agent_v4.pick_claim_file(
        files, {"config/barrel.json": 5, "src/big.ts": 5, "src/small.ts": 5}
    ) == "config/barrel.json"
    checks += 1

    # no source file at all is still None, not a crash
    assert agent_v4.pick_claim_file(["docs/x.md", "a.png"], {"docs/x.md": 9}) is None
    checks += 1

    # fetch_source must default to microsoft/vscode, or the 15 cases would
    # silently start reading a different repository
    seen = {}
    real = agent_v4.subprocess.run
    class R:
        returncode, stdout, stderr = 1, "", ""
    agent_v4.subprocess.run = lambda cmd, **kw: (seen.setdefault("cmd", cmd), R())[1]
    try:
        agent_v4.fetch_source("src/a.ts", "deadbeef", {})
        assert "repos/microsoft/vscode/contents/src/a.ts" in seen["cmd"][2], seen["cmd"]
        seen.clear()
        agent_v4.fetch_source("src/a.ts", "deadbeef", {}, "acme/widgets")
        assert "repos/acme/widgets/contents/src/a.ts" in seen["cmd"][2], seen["cmd"]
    finally:
        agent_v4.subprocess.run = real
    checks += 2

    # the cache key must include the repo, or two repos share one file's source
    c = {}
    agent_v4.fetch_source.__wrapped__ if False else None
    real = agent_v4.subprocess.run
    agent_v4.subprocess.run = lambda cmd, **kw: R()
    try:
        agent_v4.fetch_source("src/a.ts", "sha", c, "one/repo")
        agent_v4.fetch_source("src/a.ts", "sha", c, "two/repo")
    finally:
        agent_v4.subprocess.run = real
    assert len(c) == 2, f"cache collapsed two repos into one key: {c}"
    checks += 1

    print(f"eval path unchanged: {checks}/{checks} checks passed")


if __name__ == "__main__":
    main()
