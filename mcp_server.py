#!/usr/bin/env python3
"""Triage from inside the maintainer's own assistant.

A script is a thing you remember to run. An assistant is already open. This
exposes the same triage over the Model Context Protocol, so a maintainer asks
"what should I look at in vscode today" in the tool they already use, and the
answer arrives where they are.

WHY THE BROWSER PAGE STAYS. Chat is bad at tables. Nine submissions, each with
five evidence chips, a rank and a reason, is a grid, and a grid pasted into a
conversation is unreadable. So every tool returns a short summary INLINE, the
part a person actually reads in a chat window, and writes the full page beside
it and hands back the path. Summary where you are, detail where detail belongs.

WHY THERE IS NO SDK HERE. This project's reproduction promise is that a judge
clones it and runs it with the standard library and `gh`, no install step and
no account. An MCP SDK would be the first dependency and would break that for
one feature. The stdio transport is newline-delimited JSON-RPC 2.0, which is a
loop over stdin, so we write the loop. About 150 lines against a dependency
that would cost the whole project its "no install" claim.

  claude mcp add pr-slop -- python3 /abs/path/to/mcp_server.py

Nothing here can merge, close, comment or label. The tools read, and they
write one HTML file. That is the entire blast radius, and it is deliberate:
ground rule 4 wants consequential actions behind a human, and the safest way
to satisfy that is to have no consequential action to gate.
"""
import json
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

PROTOCOL = "2024-11-05"

TOOLS = [
    {
        "name": "triage_queue",
        "description": (
            "Triage the open pull requests waiting on a GitHub repository. "
            "Sorts them into predicted-merge-with-a-reported-problem, "
            "predicted-merge, and predicted-not-merged, checks every issue "
            "reference against the real repository before showing it, and "
            "returns a short summary plus the path to a full HTML page. "
            "Costs real money (roughly 0.45 USD per submission) and needs the "
            "gh CLI authenticated. Never merges, closes, comments or labels."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string",
                         "description": "owner/name, e.g. microsoft/vscode"},
                "limit": {"type": "integer", "default": 8,
                          "description": "how many open pull requests, 1 to 25"},
            },
            "required": ["repo"],
        },
    },
    {
        "name": "triage_pull_request",
        "description": (
            "Triage ONE specific pull request. What a reviewer working a queue "
            "by hand actually wants. Same evidence checks, one submission."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "owner/name"},
                "number": {"type": "integer", "description": "pull request number"},
            },
            "required": ["repo", "number"],
        },
    },
    {
        "name": "whats_new",
        "description": (
            "What changed since the last time this repository was triaged. "
            "Reads the memory store only. FREE, instant, no model calls and no "
            "network. Ask this first: if nothing is new there is nothing to "
            "pay for."),
        "inputSchema": {
            "type": "object",
            "properties": {"repo": {"type": "string", "description": "owner/name"}},
            "required": ["repo"],
        },
    },
]

GROUPS = [(1, "read first, answers a reported problem"),
          (2, "predicted merge, no reported problem cited"),
          (3, "predicted not merged"),
          (0, "could not judge")]


def _chips(f):
    bits = []
    for d in f.get("declared") or []:
        if d["status"] == "open":
            bits.append(f'author says it fixes #{d["number"]}, confirmed open')
        elif d["status"] == "missing":
            bits.append(f'author cites #{d["number"]}, WHICH DOES NOT EXIST')
        else:
            bits.append(f'author cites #{d["number"]}, {d["status"]}')
    for p in f.get("problems") or []:
        bits.append(f"cites {p}, real open issue")
    for p in f.get("invented") or []:
        bits.append(f"cites {p}, no such issue")
    c = f.get("claim")
    bits.append("code matches its description" if c is True else
                "code does NOT match its description" if c is False else
                "could not confirm the description")
    tl = f.get("test_lines")
    if tl is not None:
        bits.append(f"{tl} test lines added" if tl else "no test lines added")
    return "; ".join(bits)


def summarise(data):
    """The part a person reads in a chat window. Deliberately not a table."""
    rs = data["results"]
    out = [f'{data["repo"]}: {len(rs)} open pull requests, '
           f'read at commit {data["sha"][:8]}.']
    if data.get("prior_runs"):
        fresh = [r for r in rs if r.get("is_new")]
        out.append(f'Visit {data["prior_runs"] + 1}. '
                   + (f'{len(fresh)} new since last time: '
                      + ", ".join("#%s" % r["input"]["number"] for r in fresh)
                      if fresh else "Nothing new since last time."))
    for b, label in GROUPS:
        grp = sorted([r for r in rs if (r["verdict"].get("bucket") or 0) == b],
                     key=lambda r: r.get("rank", 999))
        if not grp:
            continue
        out.append(f"\n{label.upper()} ({len(grp)})")
        for r in grp:
            n = r["input"]["number"]
            mark = " [NEW]" if r.get("is_new") and data.get("prior_runs") else ""
            out.append(f'  #{n}{mark} {r["input"]["title"][:70]}')
            out.append(f'      {_chips(r["facts"])}')
            out.append(f'      why: {(r["verdict"].get("reason") or "")[:180]}')
    out.append(f'\nTotal {sum(r["cost"] for r in rs):.2f} USD. '
               f'Nothing was merged, closed, commented or labelled.')
    return "\n".join(out)


def _run_and_report(repo, limit=None, number=None):
    import live
    import report
    data = live.run(repo, limit or 8, False, number)
    if not data:
        return "No open pull requests found.", None
    os.makedirs(live.OUT_DIR, exist_ok=True)
    slug = repo.replace("/", "-") + (f"-pr{number}" if number else "")
    path = os.path.abspath(f"{live.OUT_DIR}/{slug}.html")
    json.dump(data, open(f"{live.OUT_DIR}/{slug}.json", "w"), indent=2, default=str)
    report.write(data, path)
    return summarise(data), path


def tool_triage_queue(args):
    limit = max(1, min(int(args.get("limit") or 8), 25))
    text, path = _run_and_report(args["repo"], limit=limit)
    return text + (f"\n\nFull page: {path}" if path else "")


def tool_triage_pull_request(args):
    text, path = _run_and_report(args["repo"], number=int(args["number"]))
    return text + (f"\n\nFull page: {path}" if path else "")


def tool_whats_new(args):
    import memory
    repo = args["repo"]
    mem = memory.load(repo)
    if not mem.get("runs"):
        return (f"{repo} has never been triaged on this machine, so there is no "
                f"'since last time'. Run triage_queue to start.")
    seen = mem.get("seen") or {}
    waiting = sorted(((v.get("times_seen", 0), k) for k, v in seen.items()
                      if v.get("was_today")), reverse=True)[:10]
    lines = [f'{repo}: {mem["runs"]} previous visits, last {mem["last_run"]}.',
             f'{len(seen)} submissions tracked, '
             f'{len(mem.get("issues") or {})} issue lookups cached.']
    if waiting:
        lines.append("\nStill open after being put in your reading list before:")
        for times, num in waiting:
            lines.append(f'  #{num}, seen on {times} visits '
                         f'(first {seen[num]["first_seen"]})')
    lines.append("\nThis read the memory store only. No model calls, no network, "
                 "no cost. Run triage_queue for a fresh look at the live queue.")
    return "\n".join(lines)


HANDLERS = {"triage_queue": tool_triage_queue,
            "triage_pull_request": tool_triage_pull_request,
            "whats_new": tool_whats_new}


def handle(msg):
    """Returns a response dict, or None for a notification."""
    method, mid = msg.get("method"), msg.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": PROTOCOL,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "pr-slop", "version": "1.0.0"}}}
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        fn = HANDLERS.get(name)
        if not fn:
            return {"jsonrpc": "2.0", "id": mid,
                    "error": {"code": -32601, "message": f"no tool named {name}"}}
        try:
            text = fn(params.get("arguments") or {})
            ok = True
        except Exception:
            # An error is content, not a transport failure: the assistant should
            # be able to read what went wrong and tell the maintainer.
            text = "Triage failed.\n" + traceback.format_exc(limit=3)
            ok = False
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "content": [{"type": "text", "text": text}], "isError": not ok}}
    if mid is None:
        return None
    return {"jsonrpc": "2.0", "id": mid,
            "error": {"code": -32601, "message": f"unknown method {method}"}}


def serve(stdin=None, stdout=None):
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle(msg)
        if resp is not None:
            stdout.write(json.dumps(resp) + "\n")
            stdout.flush()


if __name__ == "__main__":
    serve()
