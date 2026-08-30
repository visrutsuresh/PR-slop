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


def chips(f):
    out = []
    for p in f["problems"]:
        out.append(f'<span class="chip ok">fixes {esc(p)}, confirmed real</span>')
    for p in f["invented"]:
        out.append(f'<span class="chip no">claimed {esc(p)}, does not exist</span>')
    if f["claim"] is True:
        out.append('<span class="chip ok">code matches its description</span>')
    elif f["claim"] is False:
        out.append('<span class="chip no">code does not match its description</span>')
    else:
        out.append('<span class="chip hm">could not confirm the description</span>')
    out.append(f'<span class="chip {"ok" if f["has_tests"] else ""}">'
               f'{"has tests" if f["has_tests"] else "no tests"}</span>')
    out.append(f'<span class="chip">{f["lines"]} lines, {f["files"]} file'
               f'{"s" if f["files"] != 1 else ""}</span>')
    return "".join(out)


def card(r, repo):
    ci, v, f = r["input"], r["verdict"], r["facts"]
    n = ci["number"]
    strong = bool(f["problems"]) and f["claim"] is True
    flag = ""
    if strong and v.get("bucket") == 3:
        flag = ('<div class="flag">The evidence here is stronger than the '
                'suggested order implies. Worth a look before you skip it.</div>')
    return f"""<article class="pr">
  <div class="top"><span class="num">#{n}</span>
    <span class="title">{esc(ci['title'])}</span></div>
  <div class="chips">{chips(f)}</div>
  <div class="why"><b>Why:</b> {esc((v.get('reason') or '')[:280])}</div>
  <div class="links"><a href="https://github.com/{repo}/pull/{n}">open on GitHub</a></div>
  {flag}
</article>"""


GROUPS = [
    (1, "b1", "Read these first",
     "Evidence says these fix something already reported."),
    (2, "b2", "Normal queue",
     "Real work that needs your eyes. No particular urgency."),
    (3, "b3", "Leave until last",
     "Least supported by evidence. This is NOT a verdict that they are bad."),
    (0, "bx", "Could not judge",
     "Not enough evidence to place these. Shown rather than hidden."),
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
        grp.sort(key=lambda r: (-len(r["facts"]["problems"]),
                                -r["facts"]["lines"]))
        parts.append(f'<section class="group {cls}"><div class="bar"></div>'
                     f'<h2>{name} <span class="num">{len(grp)}</span></h2>'
                     f'<p>{note}</p>' +
                     "".join(card(r, repo) for r in grp) + "</section>")

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
  <div><span class="k">How to read it</span> Every claim shows its evidence.
  Anything unconfirmed says so rather than being dropped.</div>
  <div><span class="k">What it cannot do</span> It does not know your roadmap,
  your release schedule, or that you already decided against an approach. Those
  are the reasons good work gets closed, and it cannot see any of them.</div>
  <div><span class="k">Cost</span> {total:.2f} USD for {len(rs)} submissions.</div>
</div></footer></body></html>"""
    open(path, "w").write(out)
    return path


if __name__ == "__main__":
    import sys
    src = sys.argv[1]
    data = json.load(open(src))
    print(write(data, src.replace(".json", ".html")))
