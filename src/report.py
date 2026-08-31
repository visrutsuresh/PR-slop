#!/usr/bin/env python3
"""The page a maintainer opens in a browser.

Terminal output is fine for a demo and useless in a real week. This writes a
self-contained HTML file: no server, no build step, no internet. Open it, or
send it to someone.

Design rules, each from a real constraint:
  - every claim carries the evidence beside it, because a triage tool a
    maintainer cannot audit is one they will stop trusting after the first
    wrong call
  - anything the checker could not confirm is shown as unconfirmed rather than
    quietly dropped
  - nothing is ever presented as a decision. It is a reading order.
"""
import html
import json
import os

THEME = os.environ.get("PRSLOP_THEME", "paper")

# Direction A, "paper". A printed triage sheet. Warm ground, one accent, wide
# measure, generous leading. Optimised for reading a reason paragraph and for
# printing to hand to someone. Quiet on purpose: the evidence is the loud part.
CSS_PAPER = """
:root{--ink:#12100e;--paper:#faf8f4;--card:#fff;--muted:#6f6862;--line:#e6e0d6;
      --green:#1c7a4b;--amber:#b8830f;--slate:#5a6b80;--red:#b5382b}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font:400 16px/1.6 ui-sans-serif,-apple-system,"Segoe UI",Inter,system-ui,sans-serif;
  -webkit-font-smoothing:antialiased}
header{background:var(--ink);color:#f6f2ec;padding:34px 26px}
.wrap{max-width:1060px;margin:0 auto}
h1{margin:0 0 6px;font-size:27px;letter-spacing:-.02em}
header .sub{color:#a9a096;font-size:15px}
header .warn{margin-top:16px;background:#241f1a;border-left:3px solid #b8830f;
  padding:11px 15px;border-radius:0 8px 8px 0;color:#d8cfc3;font-size:14.5px}
main{padding:30px 26px 90px}
.group{margin:34px 0 10px}
.group h2{margin:0 0 3px;font-size:20px;letter-spacing:-.01em}
.group p{margin:0 0 14px;color:var(--muted);font-size:14.5px}
.bar{height:3px;border-radius:2px;margin-bottom:16px}
.b1 .bar{background:var(--green)}.b2 .bar{background:var(--amber)}
.b3 .bar{background:#c3bbb0}.bx .bar{background:var(--slate)}
.pr{background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:16px 18px;margin-bottom:11px}
.pr .top{display:flex;gap:12px;align-items:baseline;flex-wrap:wrap}
.num{font:600 14px ui-monospace,Menlo,monospace;color:var(--muted)}
.title{font-weight:650;font-size:17px;flex:1;min-width:240px}
.rank{font:600 12px ui-monospace,Menlo,monospace;color:#8a8078;background:#f2ede5;
  padding:2px 8px;border-radius:6px}
.rest{margin-top:8px}
.rest summary{cursor:pointer;color:var(--muted);font-size:14.5px;padding:9px 2px;
  list-style:revert}
.rest summary:hover{color:var(--ink)}
.chips{margin:11px 0 0;display:flex;gap:7px;flex-wrap:wrap}
.chip{font-size:13px;padding:3px 10px;border-radius:999px;background:#f2ede5;color:#5c554e}
.chip.ok{background:#e6f4ec;color:var(--green)}
.chip.no{background:#f6ece9;color:var(--red)}
.chip.hm{background:#f7f0dd;color:var(--amber)}
.why{margin:11px 0 0;color:#463f39;font-size:15px}
.why b{font-weight:650}
.links{margin:11px 0 0;font-size:14px}
a{color:#2f5d8f}
.new{display:inline-block;margin-top:7px;font-size:13px;font-weight:650;
  color:#1c7a4b;background:#e6f4ec;padding:2px 9px;border-radius:6px}
.seen{display:inline-block;margin-top:7px;font-size:13px;color:var(--muted)}
.flag{margin-top:11px;padding:10px 13px;background:#fbf6e8;border-left:3px solid var(--amber);
  border-radius:0 7px 7px 0;font-size:14.5px;color:#6b5410}
footer{border-top:1px solid var(--line);padding:26px;color:var(--muted);font-size:14px}
.k{display:inline-block;min-width:132px;color:var(--muted)}
.rev{margin-top:13px;padding:13px 15px;border-radius:10px;background:#f7f4ee;
  border:1px solid var(--line)}
.rev.q-ok{border-left:3px solid var(--green)}
.rev.q-mid{border-left:3px solid var(--amber)}
.rev.q-low{border-left:3px solid var(--red)}
.rev.q-unk{border-left:3px solid var(--slate)}
.rq{font-size:13px;color:var(--muted);letter-spacing:.01em}
.rh{margin-top:5px;font-size:15.5px;font-weight:600}
.rl{margin-top:9px;font-size:14.5px}
.rk{display:inline-block;font-size:12px;font-weight:650;text-transform:uppercase;
  letter-spacing:.07em;color:var(--muted)}
.rk.block{color:var(--red)}
.rl ul{margin:4px 0 0;padding-left:19px}
.rl li{margin:3px 0}
.why2{display:block;color:var(--muted);font-size:13.5px}
.rr{margin-top:9px;font-size:13.5px;color:#6b5410}
.rev code{font:600 13px ui-monospace,Menlo,monospace;background:#efe9df;padding:1px 5px;border-radius:4px}
.strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
  gap:1px;background:var(--line);border:1px solid var(--line);border-radius:14px;
  overflow:hidden;margin:4px 0 8px}
.cell{background:var(--card);padding:18px 20px}
.cell .n{font:650 30px/1 ui-sans-serif,system-ui;letter-spacing:-.03em}
.cell .lab{margin-top:5px;font-weight:600;font-size:14.5px}
.cell .sub{color:var(--muted);font-size:13.5px}
.group h2{position:sticky;top:0;background:var(--paper);padding:6px 0;z-index:2}
.pr:hover{border-color:#d3cabb}
a:focus-visible,summary:focus-visible{outline:2px solid var(--green);
  outline-offset:3px;border-radius:4px}
@media print{
  header{background:#fff;color:#000;border-bottom:2px solid #000}
  header .sub,header .warn{color:#333;background:#fff;border-color:#999}
  .pr{break-inside:avoid;border-color:#bbb}
  .rest[open] summary{display:none}
  .rest:not([open]){display:none}
  footer{border-color:#999}
}
"""

# Direction B, "console". Built for a maintainer who lives in a terminal and
# has sixty open submissions, not nine. Dark, monospaced, one line per
# submission with the evidence inline, so a long queue is scannable by eye
# without scrolling past card after card. Same data, opposite density.
CSS_CONSOLE = """
:root{--ink:#d7dae0;--paper:#0e1014;--card:#15181e;--muted:#7d8794;--line:#242932;
      --green:#4ec98a;--amber:#e0b341;--slate:#7f93ad;--red:#ef6a5c}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font:400 14px/1.55 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  -webkit-font-smoothing:antialiased}
header{background:#090b0e;color:var(--ink);padding:26px;border-bottom:1px solid var(--line)}
.wrap{max-width:1180px;margin:0 auto}
h1{margin:0 0 5px;font-size:20px;letter-spacing:-.01em;font-weight:600}
header .sub{color:var(--muted);font-size:13px}
header .warn{margin-top:14px;background:#12161c;border-left:2px solid var(--amber);
  padding:10px 13px;color:#b9c2cd;font-size:13px}
main{padding:22px 26px 80px}
.strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
  gap:1px;background:var(--line);border:1px solid var(--line);margin:0 0 22px}
.cell{background:var(--card);padding:14px 16px}
.cell .n{font:600 26px/1 ui-monospace,Menlo,monospace;color:var(--green)}
.cell .lab{margin-top:4px;font-size:13px;color:var(--ink)}
.cell .sub{color:var(--muted);font-size:12px}
.group{margin:26px 0 8px}
.group h2{margin:0 0 2px;font-size:13px;font-weight:600;text-transform:uppercase;
  letter-spacing:.09em;color:var(--muted);position:sticky;top:0;
  background:var(--paper);padding:6px 0;z-index:2}
.group p{margin:0 0 10px;color:var(--muted);font-size:12.5px}
.bar{height:2px;margin-bottom:12px}
.b1 .bar{background:var(--green)}.b2 .bar{background:var(--amber)}
.b3 .bar{background:#39414d}.bx .bar{background:var(--slate)}
.pr{background:var(--card);border:1px solid var(--line);border-left:2px solid var(--line);
  padding:10px 14px;margin-bottom:5px}
.b1 .pr{border-left-color:var(--green)}.b2 .pr{border-left-color:var(--amber)}
.b3 .pr{border-left-color:#39414d}
.pr:hover{background:#1a1e26}
.pr .top{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
.num{font-size:13px;color:var(--muted)}
.title{font-weight:600;font-size:14px;flex:1;min-width:220px;color:#eef1f5}
.rank{font-size:11px;color:var(--muted);background:#1d222a;padding:1px 7px}
.rest{margin-top:6px}
.rest summary{cursor:pointer;color:var(--muted);font-size:12.5px;padding:7px 2px}
.rest summary:hover{color:var(--ink)}
.chips{margin:7px 0 0;display:flex;gap:5px;flex-wrap:wrap}
.chip{font-size:12px;padding:1px 8px;background:#1d222a;color:#98a3b1}
.chip.ok{background:#12291e;color:var(--green)}
.chip.no{background:#2c1614;color:var(--red)}
.chip.hm{background:#2a2312;color:var(--amber)}
.why{margin:7px 0 0;color:#aab3bf;font-size:13px}
.why b{color:var(--ink);font-weight:600}
.links{margin:7px 0 0;font-size:12.5px}
a{color:#6fb2f0}
a:focus-visible,summary:focus-visible{outline:2px solid var(--green);outline-offset:2px}
.new{display:inline-block;margin-top:6px;font-size:12px;font-weight:600;
  color:var(--green);background:#12291e;padding:1px 8px}
.seen{display:inline-block;margin-top:6px;font-size:12px;color:var(--muted)}
.flag{margin-top:8px;padding:8px 11px;background:#221d10;border-left:2px solid var(--amber);
  font-size:12.5px;color:#dcc994}
footer{border-top:1px solid var(--line);padding:22px;color:var(--muted);font-size:12.5px}
.k{display:inline-block;min-width:132px;color:#5f6a78}
.rev{margin-top:9px;padding:10px 12px;background:#11151b;border:1px solid var(--line)}
.rev.q-ok{border-left:2px solid var(--green)}
.rev.q-mid{border-left:2px solid var(--amber)}
.rev.q-low{border-left:2px solid var(--red)}
.rev.q-unk{border-left:2px solid var(--slate)}
.rq{font-size:12px;color:var(--muted)}
.rh{margin-top:4px;font-size:13.5px;font-weight:600;color:#eef1f5}
.rl{margin-top:7px;font-size:13px}
.rk{display:inline-block;font-size:11px;font-weight:600;text-transform:uppercase;
  letter-spacing:.08em;color:var(--muted)}
.rk.block{color:var(--red)}
.rl ul{margin:3px 0 0;padding-left:17px}
.why2{display:block;color:var(--muted);font-size:12.5px}
.rr{margin-top:7px;font-size:12.5px;color:#dcc994}
.rev code{background:#1d222a;padding:1px 5px;color:#9fb6d0}
@media print{body{background:#fff;color:#000}.pr{break-inside:avoid}}
"""

CSS = CSS_CONSOLE if THEME == "console" else CSS_PAPER


def esc(s):
    return html.escape(str(s or ""))


DOT = "\u00b7"


def declared_chip(d):
    """The author's own closing reference, quoted rather than paraphrased.

    The chip leads with the quote on purpose. The pattern proves a TEXT MATCH,
    not intent, so "This does not fix #123" has to read correctly: "confirmed"
    then attaches to *the issue is open*, which is the only thing we checked.
    """
    q = (f'fact {DOT} author\u2019s text: \u201c{esc(d["quote"])}\u201d, ')
    where = "this repository" if d["same_repo"] else f'{esc(d["owner"])}/{esc(d["repo"])}'
    s = d["status"]
    if s == "open" and d["same_repo"]:
        return f'<span class="chip ok">{q}open issue, confirmed</span>'
    if s == "open":
        return f'<span class="chip ok">{q}open issue in another repo, confirmed</span>'
    if s == "closed":
        return f'<span class="chip">{q}that issue is already closed</span>'
    if s == "pull_request":
        return f'<span class="chip">{q}that number is a pull request, not an issue</span>'
    if s == "missing":
        return (f'<span class="chip no">{q}no issue #{d["number"]} in '
                f'{where}</span>')
    return f'<span class="chip hm">{q}could not reach GitHub to check</span>'


def chips(f):
    """Three categories, and the prefix is on the chip so nobody has to
    remember which is which: `fact` is re-derivable with no model at all,
    `checked` was proposed by the model and then verified against GitHub, and
    `judgement` is the model's opinion with nothing behind it."""
    out = [declared_chip(d) for d in f.get("declared") or []]
    for p in f["problems"]:
        out.append(f'<span class="chip ok">checked {DOT} cites {esc(p)}, '
                   f'real open issue</span>')
    for p in f.get("closed_refs") or []:
        out.append(f'<span class="chip">checked {DOT} cites {esc(p)}, '
                   f'real issue, already closed</span>')
    for p in f.get("pr_refs") or []:
        out.append(f'<span class="chip">checked {DOT} cites {esc(p)}, that '
                   f'number is a pull request, not an issue</span>')
    for p in f["invented"]:
        out.append(f'<span class="chip no">checked {DOT} cites {esc(p)}, '
                   f'no such issue in this repository</span>')
    for p in f.get("unresolved") or []:
        out.append(f'<span class="chip hm">checked {DOT} cites {esc(p)}, '
                   f'could not reach GitHub to confirm</span>')
    if f["claim"] is True:
        out.append(f'<span class="chip ok">judgement {DOT} code matches its '
                   f'description</span>')
    elif f["claim"] is False:
        out.append(f'<span class="chip no">judgement {DOT} code does not match '
                   f'its description</span>')
    else:
        out.append(f'<span class="chip hm">judgement {DOT} could not confirm '
                   f'the description</span>')
    # "touches a test path" was true on every card of every run so far, because
    # this repository has test directories everywhere. A chip that never varies
    # is decoration. Added test LINES varies from 3 to 550 across the same queue,
    # and it is the tell that separates a real test from a file merely brushed.
    tl = f.get("test_lines")
    if tl is None:
        out.append(f'<span class="chip {"ok" if f["has_tests"] else ""}">'
                   f'fact {DOT} {"has tests" if f["has_tests"] else "no tests"}</span>')
    elif tl:
        out.append(f'<span class="chip ok">fact {DOT} {tl} test lines added</span>')
    else:
        out.append(f'<span class="chip">fact {DOT} no test lines added</span>')
    out.append(f'<span class="chip">fact {DOT} {f["lines"]} lines added, '
               f'{f["files"]} file{"s" if f["files"] != 1 else ""}</span>')
    return "".join(out)


QUALITY_CLASS = {"solid": "q-ok", "workable": "q-mid",
                 "needs work": "q-low", "cannot tell": "q-unk"}


def review_block(rev):
    """The code review, when the tool was pointed at one submission.

    Kept visually separate from the evidence chips on purpose. The chips are
    checked facts; this is a judgement, and running them together would let a
    judgement borrow the credibility of a fact.
    """
    if not rev:
        return ""
    q = rev.get("quality") or "cannot tell"
    bits = [f'<div class="rev {QUALITY_CLASS.get(q, "q-unk")}">'
            f'<div class="rq">Code review, a judgement and not a checked fact: '
            f'<b>{esc(q)}</b></div>']
    if rev.get("headline"):
        bits.append(f'<div class="rh">{esc(rev["headline"])}</div>')
    if rev.get("blocking"):
        bits.append('<div class="rl"><span class="rk block">Blocking</span><ul>'
                    + "".join(f"<li>{esc(b)}</li>" for b in rev["blocking"])
                    + "</ul></div>")
    if rev.get("strengths"):
        bits.append('<div class="rl"><span class="rk">Does well</span><ul>'
                    + "".join(f"<li>{esc(x)}</li>" for x in rev["strengths"])
                    + "</ul></div>")
    if rev.get("improvements"):
        items = []
        for i in rev["improvements"]:
            where = (f' <code>{esc(i["where"])}</code>') if i.get("where") else ""
            why = (f'<span class="why2">{esc(i["why"])}</span>'
                   if i.get("why") else "")
            items.append(f'<li>{esc(i.get("what", ""))}{where}{why}</li>')
        bits.append('<div class="rl"><span class="rk">Could be better</span><ul>'
                    + "".join(items) + "</ul></div>")
    if rev.get("risk"):
        bits.append(f'<div class="rr">If this is wrong: {esc(rev["risk"])}</div>')
    return "".join(bits) + "</div>"


def card(r, repo, data_has_memory=False):
    ci, v, f = r["input"], r["verdict"], r["facts"]
    n = ci["number"]
    strong = (bool(f["problems"]) and f["claim"] is True) or bool(f.get("declared_ok"))
    flag = ""
    if strong and v.get("bucket") == 3:
        flag = ('<div class="flag">The evidence here is stronger than the '
                'suggested order implies. Worth a look before you skip it.</div>')
    mem = ""
    if r.get("is_new") and data_has_memory:
        mem = '<span class="new">new since your last visit</span>'
    elif (r.get("times_seen") or 0) > 1:
        n = r["times_seen"]
        extra = (", and it was in your reading list before"
                 if r.get("was_today_before") else "")
        mem = (f'<span class="seen">{n}th visit, first seen '
               f'{esc(r.get("first_seen"))}{extra}</span>')
    rankbadge = (f'<span class="rank">{r["rank"]} of {r["group_size"]}</span>'
                 if r.get("group_size", 0) > 1 else "")
    return f"""<article class="pr">
  <div class="top"><span class="num">#{n}</span>{rankbadge}
    <span class="title">{esc(ci['title'])}</span></div>
  {mem}
  <div class="chips">{chips(f)}</div>
  <div class="why"><b>Why:</b> {esc((v.get('reason') or '')[:280])}</div>
  <div class="links"><a href="https://github.com/{repo}/pull/{n}">open on GitHub</a></div>
  {flag}
  {review_block(r.get("review"))}
</article>"""


# Which group a submission lands in is a PREDICTION about the merge decision,
# which is what the model was actually asked for. The earlier headings named a
# reading order instead ("Read these first", "Leave until last"), a different
# claim from the one behind them.
GROUPS = [
    (1, "b1", "Predicted merge, and the model tied it to an already-reported "
     "problem",
     "A prediction about what a maintainer would decide, not a measurement. "
     "The link to a reported problem is the model's, checked against GitHub "
     "before you saw it. The order inside the group is evidence strength."),
    (2, "b2", "Predicted merge, with no reported problem cited by the model",
     "Same prediction, without the model finding and citing an already-"
     "reported problem for it. That describes the model's search, not the "
     "world: a card below can still carry the author's own declared "
     "reference, which is machine-derived and does not move the group. The "
     "order inside the group is evidence strength."),
    (3, "b3", "Predicted not merged",
     "A prediction about a human decision, NOT a judgement that the work is "
     "bad. Housekeeping, superseded work and duplicates all land here."),
    (0, "bx", "No prediction either way",
     "The model declined to call these rather than guess, which says nothing "
     "about the evidence on the cards below. Shown rather than hidden."),
]


def write(data, path):
    repo = data["repo"]
    rs = data["results"]
    # "new" only means something once there is a previous visit to be new since.
    has_mem = bool(data.get("prior_runs"))
    total = sum(r["cost"] for r in rs)
    parts = []
    for b, cls, name, note in GROUPS:
        grp = [r for r in rs if (r["verdict"].get("bucket") or 0) == b]
        if not grp:
            continue
        grp.sort(key=lambda r: r.get("rank", 999))
        today = [r for r in grp if r.get("today", True)]
        later = [r for r in grp if not r.get("today", True)]
        head = (f'<section class="group {cls}"><div class="bar"></div>'
                f'<h2>{name} <span class="num">{len(grp)}</span></h2>'
                f'<p>{note}</p>')
        body_html = "".join(card(r, repo, has_mem) for r in today)
        if later:
            body_html += (
                f'<details class="rest"><summary>{len(later)} more in this '
                f'group, ordered by checked evidence, then by how recent they '
                f'are. Nothing is hidden, this is just not today\'s '
                f'reading.</summary>'
                + "".join(card(r, repo, has_mem) for r in later) + "</details>")
        parts.append(head + body_html + "</section>")

    body = "\n".join(parts)

    # The one thing a maintainer wants before reading anything: how much of
    # this is actually mine to do today, and what changed since last time.
    first = [r for r in rs if (r["verdict"].get("bucket") or 0) == 1]
    fresh = [r for r in rs if r.get("is_new")] if has_mem else []
    weak = [r for r in rs
            if any(d["status"] == "missing" for d in (r["facts"].get("declared") or []))
            or r["facts"].get("invented")]
    cells = [("Read first", len(first), "answer a reported problem"),
             ("In the queue", len(rs), "open right now")]
    if has_mem:
        cells.insert(1, ("New since last visit", len(fresh),
                         f'visit {data.get("prior_runs", 0) + 1}'))
    if weak:
        cells.append(("Cite an issue that does not exist", len(weak),
                      "worth a closer look"))
    strip = '<div class="strip">' + "".join(
        f'<div class="cell"><div class="n">{v}</div>'
        f'<div class="lab">{esc(k)}</div><div class="sub">{esc(sub)}</div></div>'
        for k, v, sub in cells) + "</div>"
    body = strip + body
    out = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Triage, {esc(repo)}</title><style>{CSS}</style></head><body>
<header><div class="wrap">
  <h1>{esc(repo)}, {len(rs)} open pull requests</h1>
  <div class="sub">A suggested reading order. Generated {esc(data['generated'])}.</div>
  <div class="warn"><b>Nothing here has been acted on.</b> This tool cannot
  merge, close, comment or label. It read {data['corpus']} of your recorded
  problems and the code at commit <code>{esc(data['sha'][:8])}</code>, and
  every reference below was checked before you saw it. The order is a
  suggestion; you decide.</div>
</div></header>
<main><div class="wrap">{body}</div></main>
<footer><div class="wrap">
  <div><span class="k">The groups</span> Which group a submission is in is a
  <em>prediction</em> about the decision a maintainer would make, not a
  measurement and not a quality verdict. The order <em>inside</em> a group is a
  different thing: evidence strength, described next.</div>
  <div><span class="k">The order</span> Within each group, by how much
  <em>checked</em> evidence supports it: a reference the author declared and we
  confirmed, then a confirmed link to an already-reported problem, then a
  confirmed description. Ties break to the newer submission, which is recency,
  not evidence. Tests and size do not affect the order; they are shown, not
  ranked.</div>
  <div><span class="k">How to read it</span> Chips marked <em>fact</em> you can
  re-derive yourself from GitHub with no model involved: files changed, lines
  added, whether test paths are touched, and any closing reference found in the
  author's own title or body, quoted verbatim. That last one is a <b>text
  match, not a statement of intent</b>: the tool reports the characters the
  author wrote and whether the referenced issue is real and open. It does not
  read the sentence around them, so a negation ("does not fix #123") or an
  unticked template checkbox will still show a chip; a reference inside a
  fenced code block is skipped. The quote is there so you can see which one you
  are looking at. Chips marked <em>checked</em> were proposed by the model and
  then verified against GitHub, so the reference is real and its state is
  accurate, but the model chose to cite it. Chips marked <em>judgement</em> are
  the model's opinion and nothing verified them. The order on this page puts
  checked evidence first and breaks ties by recency, not an accuracy claim: these pull
  requests are open, so no correct answer exists to score against.</div>
  <div><span class="k">What it cannot do</span> It does not know your roadmap,
  your release schedule, or that you already decided against an approach. Those
  are the reasons good work gets closed, and it cannot see any of them.</div>
  <div><span class="k">This run</span> {esc(repo)}, {len(rs)} submissions,
  generated {esc(data['generated'])}, source read at commit
  <code>{esc(data['sha'][:8])}</code>, {total:.2f} USD.</div>
</div></footer></body></html>"""
    open(path, "w").write(out)
    return path


if __name__ == "__main__":
    import sys
    src = sys.argv[1]
    data = json.load(open(src))
    print(write(data, src.replace(".json", ".html")))
