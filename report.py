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

CSS = """
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
.flag{margin-top:11px;padding:10px 13px;background:#fbf6e8;border-left:3px solid var(--amber);
  border-radius:0 7px 7px 0;font-size:14.5px;color:#6b5410}
footer{border-top:1px solid var(--line);padding:26px;color:var(--muted);font-size:14px}
.k{display:inline-block;min-width:132px;color:var(--muted)}
"""


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
    out.append(f'<span class="chip {"ok" if f["has_tests"] else ""}">'
               f'fact {DOT} {"has tests" if f["has_tests"] else "no tests"}</span>')
    out.append(f'<span class="chip">fact {DOT} {f["lines"]} lines added, '
               f'{f["files"]} file{"s" if f["files"] != 1 else ""}</span>')
    return "".join(out)


def card(r, repo):
    ci, v, f = r["input"], r["verdict"], r["facts"]
    n = ci["number"]
    strong = (bool(f["problems"]) and f["claim"] is True) or bool(f.get("declared_ok"))
    flag = ""
    if strong and v.get("bucket") == 3:
        flag = ('<div class="flag">The evidence here is stronger than the '
                'suggested order implies. Worth a look before you skip it.</div>')
    rankbadge = (f'<span class="rank">{r["rank"]} of {r["group_size"]}</span>'
                 if r.get("group_size", 0) > 1 else "")
    return f"""<article class="pr">
  <div class="top"><span class="num">#{n}</span>{rankbadge}
    <span class="title">{esc(ci['title'])}</span></div>
  <div class="chips">{chips(f)}</div>
  <div class="why"><b>Why:</b> {esc((v.get('reason') or '')[:280])}</div>
  <div class="links"><a href="https://github.com/{repo}/pull/{n}">open on GitHub</a></div>
  {flag}
</article>"""


# Which group a submission lands in is a PREDICTION about the merge decision,
# which is what the model was actually asked for. The earlier headings named a
# reading order instead ("Read these first", "Leave until last"), a different
# claim from the one behind them.
GROUPS = [
    (1, "b1", "Predicted merge, and it answers something already reported",
     "A prediction about what a maintainer would decide, not a measurement. "
     "The order inside the group is evidence strength."),
    (2, "b2", "Predicted merge, with nothing reported to attach it to",
     "Same prediction, minus the link to an already-reported problem. The "
     "order inside the group is evidence strength."),
    (3, "b3", "Predicted not merged",
     "A prediction about a human decision, NOT a judgement that the work is "
     "bad. Housekeeping, superseded work and duplicates all land here."),
    (0, "bx", "Not enough evidence to predict either way",
     "The model declined to call these rather than guess. Shown rather than "
     "hidden."),
]


def write(data, path):
    repo = data["repo"]
    rs = data["results"]
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
        body_html = "".join(card(r, repo) for r in today)
        if later:
            body_html += (
                f'<details class="rest"><summary>{len(later)} more in this '
                f'group, ordered by checked evidence, then by how recent they '
                f'are. Nothing is hidden, this is just not today\'s '
                f'reading.</summary>'
                + "".join(card(r, repo) for r in later) + "</details>")
        parts.append(head + body_html + "</section>")

    body = "\n".join(parts)
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
