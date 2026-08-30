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
    memory_checks()
    mcp_checks()




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




def memory_checks():
    """Memory is only allowed to carry FACTS forward. These pin that."""
    import tempfile, shutil, memory
    checks = 0
    tmp = tempfile.mkdtemp()
    old_dir = memory.MEM_DIR
    memory.MEM_DIR = tmp
    try:
        # first visit: everything is new, nothing was seen before
        mem = memory.load("o/r")
        assert mem["runs"] == 0 and mem["seen"] == {}
        rs = [{"input": {"number": 1}, "today": True},
              {"input": {"number": 2}, "today": False}]
        memory.annotate(mem, rs)
        assert all(r["is_new"] for r in rs), rs
        assert all(r["times_seen"] == 1 for r in rs)
        assert memory.save(mem)
        checks += 1

        # second visit: #1 is not new, #3 is, and the count advances
        mem2 = memory.load("o/r")
        assert mem2["runs"] == 1, mem2["runs"]
        rs2 = [{"input": {"number": 1}, "today": False},
               {"input": {"number": 3}, "today": True}]
        memory.annotate(mem2, rs2)
        by = {r["input"]["number"]: r for r in rs2}
        assert by[1]["is_new"] is False and by[1]["times_seen"] == 2, rs2
        assert by[3]["is_new"] is True
        # #1 was in the reading list on visit one, and that must survive
        assert by[1]["was_today_before"] is True, by[1]
        checks += 1

        # a resolved issue state is a fact and is reusable
        memory.remember_issue(mem2, "o/r", 42, "open")
        assert memory.cached_issue(mem2, "o/r", 42) == "open"
        checks += 1

        # but "we could not reach GitHub" is NOT a fact, and caching it would
        # let one rate-limited run poison every later run
        memory.remember_issue(mem2, "o/r", 43, "unresolved")
        assert memory.cached_issue(mem2, "o/r", 43) is None
        checks += 1

        # a corrupt store must degrade to no-memory, never crash the run
        with open(memory._path("o/r"), "w") as fh:
            fh.write("{ this is not json")
        broken = memory.load("o/r")
        assert broken["runs"] == 0 and broken["seen"] == {}, broken
        checks += 1

        # an unwritable store must not fail the run
        memory.MEM_DIR = "/proc/nonexistent-cannot-create"
        assert memory.save(memory._empty("o/r")) is False
        checks += 1
    finally:
        memory.MEM_DIR = old_dir
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"memory: {checks}/{checks} checks passed")




def mcp_checks():
    """The protocol surface, exercised without a network call or a model call."""
    import io, sys, json as J, mcp_server
    checks = 0

    def rpc(*msgs):
        out = io.StringIO()
        mcp_server.serve(io.StringIO("\n".join(J.dumps(m) for m in msgs)), out)
        return [J.loads(l) for l in out.getvalue().splitlines() if l.strip()]

    # handshake returns the protocol version and declares the tools capability
    r = rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})[0]
    assert r["result"]["protocolVersion"] == mcp_server.PROTOCOL
    assert "tools" in r["result"]["capabilities"]
    checks += 1

    # a notification gets NO response; replying to one corrupts the stream
    assert rpc({"jsonrpc": "2.0", "method": "notifications/initialized"}) == []
    checks += 1

    # every advertised tool has a handler, and every handler is advertised
    r = rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})[0]
    names = {t["name"] for t in r["result"]["tools"]}
    assert names == set(mcp_server.HANDLERS), (names, set(mcp_server.HANDLERS))
    for t in r["result"]["tools"]:
        assert t["inputSchema"]["type"] == "object"
        for req in t["inputSchema"].get("required", []):
            assert req in t["inputSchema"]["properties"], (t["name"], req)
    checks += 1

    # an unknown tool is a JSON-RPC error, not a crash
    r = rpc({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "does_not_exist", "arguments": {}}})[0]
    assert r["error"]["code"] == -32601
    checks += 1

    # a tool that raises returns isError content, so the assistant can read the
    # failure and tell the maintainer, rather than the transport dying
    boom = lambda a: (_ for _ in ()).throw(RuntimeError("kaboom"))
    mcp_server.HANDLERS["_boom"] = boom
    try:
        r = rpc({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                 "params": {"name": "_boom", "arguments": {}}})[0]
        assert r["result"]["isError"] is True
        assert "kaboom" in r["result"]["content"][0]["text"]
    finally:
        del mcp_server.HANDLERS["_boom"]
    checks += 1

    # malformed input must not kill the loop: the good message still answers
    out = io.StringIO()
    mcp_server.serve(io.StringIO('not json\n\n{"jsonrpc":"2.0","id":9,'
                                 '"method":"tools/list"}\n'), out)
    got = [J.loads(l) for l in out.getvalue().splitlines() if l.strip()]
    assert len(got) == 1 and got[0]["id"] == 9, got
    checks += 1

    # the inline summary must never imply an action was taken
    import memory, tempfile
    old = memory.MEM_DIR
    memory.MEM_DIR = tempfile.mkdtemp()
    try:
        # data/, not reports/. reports/* is gitignored, so reading from there
        # passes on a machine that has paid for a live run and crashes on a
        # fresh clone, taking every check below it down with set -e.
        data = J.load(open("data/live-record-prefix.json"))
        text = mcp_server.summarise(data)
        assert "Nothing was merged, closed, commented or labelled." in text
        assert "USD" in text
    finally:
        memory.MEM_DIR = old
    checks += 1

    # STDOUT IS THE PROTOCOL. A tool that prints progress with plain print()
    # injects raw text into the JSON-RPC stream and corrupts the session on the
    # first real call. This shipped broken: the handler tests above all passed
    # because none of them reaches the code that prints. Every line stdout
    # carries must be valid JSON.
    def noisy(args):
        print("[live] fetching open pull requests from somewhere")
        print("[live] 300 recorded problems")
        return "done"
    mcp_server.HANDLERS["_noisy"] = noisy
    try:
        # In production serve() writes to sys.stdout and print() ALSO goes to
        # sys.stdout, which is why they collide. An earlier version of this
        # check passed a separate StringIO, so the two never shared a stream
        # and the check could not fail. Bind them to the same stream, the way
        # the real server runs.
        out = io.StringIO()
        real = sys.stdout
        sys.stdout = out
        try:
            mcp_server.serve(io.StringIO(J.dumps(
                {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                 "params": {"name": "_noisy", "arguments": {}}})), out)
        finally:
            sys.stdout = real
        lines = [l for l in out.getvalue().splitlines() if l.strip()]
        for l in lines:
            J.loads(l)   # raises if a tool leaked plain text onto stdout
        assert len(lines) == 1, f"tool output leaked onto the protocol: {lines}"
        assert J.loads(lines[0])["result"]["content"][0]["text"] == "done"
    finally:
        del mcp_server.HANDLERS["_noisy"]
    checks += 1

    # --- the configurable output surface ---------------------------------
    captured = {}

    def fake_run(repo, limit, drafts, only=None, review=None, scan_all=False):
        captured.update(repo=repo, limit=limit, only=only, review=review,
                        scan_all=scan_all)
        return {"repo": repo, "sha": "deadbeef1234", "corpus": 0,
                "generated": "now", "results": [
                    {"input": {"number": 7, "title": "t"},
                     "verdict": {"bucket": 2, "reason": "r"},
                     "facts": {"problems": [], "invented": [], "declared": [],
                               "claim": True, "has_tests": True, "files": 1,
                               "lines": 1, "test_lines": 0},
                     "review": {"quality": "needs work",
                                "headline": "does one thing twice",
                                "improvements": [{"what": "dedupe it",
                                                  "why": "it drifts",
                                                  "where": "a.ts"}],
                                "blocking": [], "strengths": [], "risk": "low"},
                     "cost": 0.1, "searches": 1, "rank": 1, "group_size": 1,
                     "today": True}]}

    import live as _live
    real_run = _live.run
    _live.run = fake_run
    try:
        # single-PR mode turns the code review ON without being asked
        t = mcp_server.tool_triage_pull_request({"repo": "o/r", "number": 7})
        assert captured["review"] is True, captured
        assert "CODE REVIEW: NEEDS WORK" in t, t
        assert "dedupe it" in t and "because it drifts" in t, t
        checks += 1

        # and can be turned off explicitly
        mcp_server.tool_triage_pull_request({"repo": "o/r", "number": 7,
                                             "review": False})
        assert captured["review"] is False, captured
        checks += 1

        # a queue scan does NOT pay for a per-submission review
        mcp_server.tool_triage_queue({"repo": "o/r", "limit": 3,
                                      "confirm_cost": True})
        assert captured["review"] is None and captured["scan_all"] is False
        assert captured["limit"] == 3
        checks += 1

        # output=report hands back a path and NOT the wall of text
        t = mcp_server.tool_triage_pull_request({"repo": "o/r", "number": 7,
                                                 "output": "report"})
        assert ".html" in t and "CODE REVIEW" not in t, t
        checks += 1

        # output=both carries the summary AND the path
        t = mcp_server.tool_triage_pull_request({"repo": "o/r", "number": 7,
                                                 "output": "both"})
        assert "CODE REVIEW" in t and ".html" in t, t
        checks += 1

        # inline is the summary and NOTHING else. This assertion existed
        # before and could not fail, because inline appended the path exactly
        # like both, so the two modes were one and the check asserted on a
        # string every branch produced.
        t = mcp_server.tool_triage_pull_request({"repo": "o/r", "number": 7,
                                                 "output": "inline"})
        assert "CODE REVIEW" in t and ".html" not in t, t
        checks += 1

        # the three advertised modes must be three distinct outputs
        a, b, c = (mcp_server.tool_triage_pull_request(
            {"repo": "o/r", "number": 7, "output": m})
            for m in ("inline", "report", "both"))
        assert a != b and b != c and a != c, (a, b, c)
        checks += 1

        # an unknown mode degrades to inline rather than exploding. This is
        # _shape's fallthrough, not a whitelist: the whitelist that used to sit
        # in _mode was deleted because it was unreachable and this check could
        # not tell the difference.
        t = mcp_server.tool_triage_pull_request({"repo": "o/r", "number": 7,
                                                 "output": "interpretive-dance"})
        assert t == a, (t, a)
        checks += 1
    finally:
        _live.run = real_run

    # the DEFAULT depth is now 100, which is a real bill, so an unconfirmed
    # call must quote it and spend nothing. A judge typing the obvious command
    # should not find out the price afterwards.
    t = mcp_server.tool_triage_queue({"repo": "o/r"})
    assert "Nothing has been spent" in t and "confirm_cost" in t, t
    # every offered depth must carry its own price, or the choice is not a real
    # one: "100" means nothing to someone who has not priced a run
    for n, usd in ((5, "2.25"), (25, "11.25"), (100, "45.00")):
        assert str(n) in t and usd in t, (n, usd, t)
    assert "whats_new is free" in t, t
    checks += 1

    # the option set is data, so both surfaces can offer the same choice
    import live as _l
    opts = _l.depth_options("o/r", 1782)
    assert [o["n"] for o in opts] == [5, 25, 100, 1782], opts
    assert opts[-1]["usd"] == round(1782 * 0.45, 2), opts[-1]
    # a repository smaller than an option must not be offered that option
    small = _l.depth_options("o/r", 7)
    assert [o["n"] for o in small] == [5, 7], small
    checks += 1

    # a small ask is under the line and runs without ceremony
    _live2 = _live.run
    _live.run = fake_run
    try:
        t = mcp_server.tool_triage_queue({"repo": "o/r", "limit": 5})
        assert "Nothing has been spent" not in t, t
    finally:
        _live.run = _live2
    checks += 1

    # a full scan must refuse and quote the bill before spending it
    real_fetch = _live.count_open_prs
    _live.count_open_prs = lambda repo, drafts=False: 1782
    try:
        t = mcp_server.tool_triage_queue({"repo": "o/r", "scan_all": True})
        assert "1782" in t, t                      # the real size, not a guess
        assert "801.90" in t or "801.9" in t, t    # 1782 * 0.45, priced honestly
        assert "Nothing has been spent" in t and "confirm_cost" in t, t
    finally:
        _live.count_open_prs = real_fetch
    checks += 1

    # THE GUARD MUST FAIL CLOSED. The size comes from the search index and the
    # paid run paginates REST, so the two can disagree. A search index that
    # lags or soft-errors to 0 must never wave through a full scan: that is an
    # 800 USD run with no bill quoted. This shipped broken for one commit.
    real_count = _live.count_open_prs
    try:
        for fake in (0, 1, 10, _live.CONFIRM_ABOVE):
            _live.count_open_prs = lambda repo, drafts=False, _f=fake: _f
            t = mcp_server.tool_triage_queue({"repo": "o/r", "scan_all": True})
            assert "Nothing has been spent" in t, (fake, t)
    finally:
        _live.count_open_prs = real_count
    checks += 1

    # typing 0 means NONE, not a paid one-submission run. The check that used
    # to sit here asserted only that ask_depth had a docstring, which is the
    # fifth decoration found in this project and the reason every check now
    # gets broken on purpose before it is believed.
    import io as _io
    real_stdin, real_in = sys.stdin, __builtins__.input if hasattr(__builtins__, "input") else None
    class _TTY(_io.StringIO):
        def isatty(self):
            return True
    cases = {"0": 0, " 0 ": 0, "-5": 0, "n": 0, "cancel": 0,
             "garbage": 0, "": 25, "7": 7}
    try:
        for typed, want in cases.items():
            sys.stdin = _TTY()
            import builtins
            builtins.input = lambda _p="", _t=typed: _t
            got = _live.ask_depth("o/r", _live.depth_options("o/r", 100), 100)
            assert got == want, f"typed {typed!r} -> {got}, wanted {want}"
    finally:
        sys.stdin = real_stdin
        import builtins
        builtins.input = real_in or builtins.input
    checks += 1

    # the size is fetched in ONE call, not by paginating the whole queue. That
    # cost ~36 API calls and 48 seconds purely to say "too expensive to run",
    # which reads as a hang and pays the same bill twice.
    calls = []
    real_run = _live.subprocess.run
    class _R:
        returncode, stdout, stderr = 0, "1782", ""
    _live.subprocess.run = lambda cmd, **kw: (calls.append(cmd), _R())[1]
    try:
        assert _live.count_open_prs("o/r") == 1782
    finally:
        _live.subprocess.run = real_run
    assert len(calls) == 1, f"expected one call, made {len(calls)}"
    assert "search/issues" in calls[0], calls[0]
    assert any("-is:draft" in str(c) for c in calls[0]), calls[0]
    checks += 1

    print(f"mcp server: {checks}/{checks} checks passed")


if __name__ == "__main__":
    main()
