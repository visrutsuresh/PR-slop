#!/usr/bin/env python3
"""The page a maintainer opens in a browser.

Terminal output is fine for a demo and useless in a real week. This writes a
self-contained HTML file: no server, no build step, no internet. Open it, or
send it to someone.

A kanban board of predictions; click a card to open a Notion-style detail
page for that pull request; a back arrow returns to the board. One file,
swapped by inline JS: no router, no build step, opens from file://.

Design rules, each from a real constraint:
  - every claim carries the evidence beside it, because a triage tool a
    maintainer cannot audit is one they will stop trusting after the first
    wrong call
  - anything the checker could not confirm is shown as unconfirmed rather than
    quietly dropped
  - nothing is ever presented as a decision. It is a reading order.
  - every mark on the board and the page is derived from the record; none is
    a literal, because a hardcoded mark is the same defect as a dropped
    record: both let the page say something the data does not support.
"""
import html
import json


def esc(s):
    return html.escape(str(s or ""))


# --- marks: fact square / checked diamond / judgement circle. shape and fill
# carry the state; colour is reinforcement only, so this survives greyscale
# and deuteranopia. ---------------------------------------------------------
def mk_fact():
    return '<span class="mk mk-fact" aria-hidden="true"></span>'


def mk_checked(sub):
    return f'<span class="mk mk-checked mk-{sub}" aria-hidden="true"></span>'


def mk_judge(sub):
    return f'<span class="mk mk-judge mk-j-{sub}" aria-hidden="true"></span>'


def evidence_rows(f):
    """Returns (tier, mark_html, text) rows for a pull request's Evidence
    section: fact, checked, judgement, in that grouping.

    A declared closing reference is worded the same way the flat report's
    own chip worded it ("author's text: ..."), because IMPROVEMENT-CHANGELOG.md
    quotes that exact phrase as what the page shows. Changing the wording
    would make a shipped doc claim false with nothing left to catch it.
    """
    rows = []
    for d in f["declared"]:
        q = f'author’s text: “{esc(d["quote"])}”'
        where = "this repo" if d["same_repo"] else f'{esc(d["owner"])}/{esc(d["repo"])}'
        s = d["status"]
        if s == "open" and d["same_repo"]:
            rows.append(("checked", mk_checked("solid"), f'{q}, open issue, confirmed'))
        elif s == "open":
            rows.append(("checked", mk_checked("solid"), f'{q}, open issue in another repo, confirmed'))
        elif s == "closed":
            rows.append(("checked", mk_checked("hollow"), f'{q}, that issue is already closed'))
        elif s == "pull_request":
            rows.append(("checked", mk_checked("hollow"), f'{q}, that number is a pull request, not an issue'))
        elif s == "missing":
            rows.append(("checked", mk_checked("crossed"), f'{q}, no issue #{d["number"]} in {where}'))
        else:
            rows.append(("checked", mk_checked("dashed"), f'{q}, could not reach GitHub to check'))
    for p in f["problems"]:
        rows.append(("checked", mk_checked("solid"), f'cited {esc(p)} as the problem this fixes: open, confirmed'))
    for p in f.get("closed_refs") or []:
        rows.append(("checked", mk_checked("hollow"), f'cited {esc(p)}: real, already closed'))
    for p in f.get("pr_refs") or []:
        rows.append(("checked", mk_checked("hollow"), f'cited {esc(p)}: a pull request, not an issue'))
    for p in f["invented"]:
        rows.append(("checked", mk_checked("crossed"), f'cited {esc(p)}: no such issue exists here'))
    for p in f.get("unresolved") or []:
        rows.append(("checked", mk_checked("dashed"), f'cited {esc(p)}: could not confirm'))
    claim = f["claim"]
    if claim is True:
        rows.append(("judgement", mk_judge("match"), "the code matches its own description"))
    elif claim is False:
        rows.append(("judgement", mk_judge("nomatch"), "the code does not match its own description"))
    else:
        rows.append(("judgement", mk_judge("unclear"), "cannot confirm the code matches its description"))
    tl = f.get("test_lines")
    if tl is None:
        rows.append(("fact", mk_fact(), "has test files" if f["has_tests"] else "touches no test files"))
    elif tl:
        rows.append(("fact", mk_fact(), f"{tl} test lines added"))
    else:
        rows.append(("fact", mk_fact(), "no test lines added, despite touching a test path"
                     if f["has_tests"] else "no test lines added"))
    rows.append(("fact", mk_fact(), f'{f["lines"]} lines changed, {f["files"]} file{"s" if f["files"] != 1 else ""}'))
    return rows


def tier_counts(f):
    rows = evidence_rows(f)
    n_fact = sum(1 for t, _, _ in rows if t == "fact")
    n_checked = sum(1 for t, _, _ in rows if t == "checked")
    n_judge = sum(1 for t, _, _ in rows if t == "judgement")
    checked_bad = any(t == "checked" and "crossed" in m for t, m, _ in rows)
    return n_fact, n_checked, n_judge, checked_bad


def compact_summary(f):
    """Labelled chip per tier, always visible text, not tooltip-only.

    Every mark here is DERIVED from the data. Nothing is a literal. A board
    card and its own detail page must never disagree: an earlier draft drew
    a "matches" circle on a pull request whose page said the code does not
    match its description, because this function hardcoded the state.
    """
    n_fact, n_checked, n_judge, checked_bad = tier_counts(f)
    rows = evidence_rows(f)

    claim = f["claim"]
    j_sub = "match" if claim is True else ("nomatch" if claim is False else "unclear")

    # checked: show the WORST state present, so one bad reference stays
    # visible on the board instead of being averaged away by good ones
    subs = [m for t, m, _ in rows if t == "checked"]
    checked_mark = ""
    if subs:
        for cand in ("crossed", "dashed", "hollow", "solid"):
            if any(f'mk-{cand}"' in m for m in subs):
                checked_mark = mk_checked(cand)
                break
    else:
        # nothing verified: a neutral placeholder, never the filled
        # "confirmed" diamond next to a zero
        checked_mark = '<span class="mk mk-empty" aria-hidden="true"></span>'

    bad_cls = " chip-flag" if checked_bad else ""
    empty_cls = " chip-empty" if not n_checked else ""
    return (
        f'<span class="chip chip-fact">{mk_fact()}{n_fact} fact</span>'
        f'<span class="chip chip-checked{bad_cls}{empty_cls}">{checked_mark}{n_checked} checked</span>'
        f'<span class="chip chip-judge">{mk_judge(j_sub)}{n_judge} judgement</span>'
    )


def is_strong(f):
    return bool(f["problems"]) or bool(f.get("declared_ok"))


def anchor_id(n):
    return f"pr-{n}"


# Which group a submission lands in is a PREDICTION about the merge decision.
# Bucket 0 is a real, distinct outcome (the model declined to call it) and
# must keep its own column: dropping it silently loses an undecided pull
# request the same way a hardcoded mark loses the true state.
BUCKET_META = {
    1: ("Merge predicted, issue confirmed", "Tied to a filed, open issue."),
    2: ("Merge predicted, no issue found", "No confirmed issue behind it."),
    3: ("Merge unlikely", "Housekeeping and superseded work land here too."),
    0: ("No prediction either way", "The model declined to guess. Shown rather than hidden."),
}
BUCKET_ORDER = [1, 2, 3, 0]


def card_html(r, repo):
    ci = r["input"]
    n = ci["number"]
    f = r["facts"]
    bucket = r["verdict"].get("bucket") or 0
    flag = ""
    if is_strong(f) and bucket == 3:
        flag = '<div class="cflag">Stronger evidence than this pile suggests.</div>'
    group_size = r.get("group_size") or 1
    rank_txt = f'{r["rank"]} of {group_size}' if group_size > 1 else "1 of 1"
    return f'''<button class="card" data-target="{anchor_id(n)}" aria-haspopup="true">
  <div class="card-top"><span class="num">#{n}</span><span class="rank">{esc(rank_txt)}</span></div>
  <div class="card-title">{esc(ci["title"])}</div>
  <div class="card-evidence">{compact_summary(f)}</div>
  {flag}
</button>'''


def summary_strip(data, rs, has_mem):
    """The one thing a maintainer wants before reading anything: how much of
    this is actually theirs to do today, and what changed since last time."""
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
    return '<div class="strip">' + "".join(
        f'<div class="cell"><div class="n">{v}</div>'
        f'<div class="lab">{esc(k)}</div><div class="sub">{esc(sub)}</div></div>'
        for k, v, sub in cells) + "</div>"


def board_html(data, rs, has_mem):
    repo = data["repo"]
    cols = []
    for b in BUCKET_ORDER:
        name, note = BUCKET_META[b]
        items = [r for r in rs if (r["verdict"].get("bucket") or 0) == b]
        if not items:
            continue
        items.sort(key=lambda r: r.get("rank") or 999)
        today = [r for r in items if r.get("today", True)]
        later = [r for r in items if not r.get("today", True)]
        cards = "".join(card_html(r, repo) for r in today)
        more = ""
        if later:
            more = (f'<details class="col-more"><summary>{len(later)} more in '
                    f'this column, ordered by checked evidence, then by how '
                    f"recent they are. Nothing is hidden, this is just not "
                    f"today's reading.</summary>"
                    f'<div class="col-cards">{"".join(card_html(r, repo) for r in later)}</div>'
                    '</details>')
        cols.append(f'''<section class="col" aria-label="{esc(name)}">
  <header class="col-head"><h2>{esc(name)}</h2><span class="count">{len(items)}</span></header>
  <p class="col-note">{esc(note)}</p>
  <div class="col-cards">{cards}</div>
  {more}
</section>''')
    total = sum(r["cost"] for r in rs)
    return f'''<div class="board" id="board" role="region" aria-label="Kanban board">
  <header class="board-head">
    <h1>{esc(repo)}, {len(rs)} open pull requests</h1>
    <p class="board-sub">Read-only. Generated {esc(data["generated"])}, commit <code>{esc(data["sha"][:8])}</code>.</p>
  </header>
  {summary_strip(data, rs, has_mem)}
  <div class="board-cols">{"".join(cols)}</div>
  <footer class="board-foot">Checked against {data["corpus"]} known issues, {total:.2f} USD this run.
  This ranking is a suggestion, not a decision.</footer>
</div>'''


def properties_rows(r, sha8):
    bucket = r["verdict"].get("bucket") or 0
    name, _ = BUCKET_META[bucket]
    group_size = r.get("group_size") or 1
    rank_txt = f'{r["rank"]} of {group_size}' if group_size > 1 else "1 of 1"
    f = r["facts"]
    p = r.get("pr") or {}
    user = (p.get("user") or {}).get("login") or "not recorded"
    created = p.get("created_at")
    updated = p.get("updated_at")
    conf = r["verdict"].get("confidence") or r.get("confidence") or "none given"
    return [
        ("Status", esc(name)),
        ("Rank", esc(rank_txt)),
        ("Confidence", esc(conf)),
        ("Author", esc(user)),
        ("Files", str(f["files"])),
        ("Lines", str(f["lines"])),
        ("Test lines", str(f.get("test_lines")) if f.get("test_lines") is not None
         else ("some" if f["has_tests"] else "none")),
        ("Opened", esc(created[:10]) if created else "not recorded"),
        ("Updated", esc(updated[:10]) if updated else "not recorded"),
        ("Commit", f'<code>{esc(sha8)}</code>'),
    ]


def properties_html(r, sha8):
    rows = "".join(f'<div class="prop-row"><span class="prop-k">{k}</span><span class="prop-v">{v}</span></div>'
                   for k, v in properties_rows(r, sha8))
    return f'<div class="props">{rows}</div>'


def evidence_section_html(r):
    f = r["facts"]
    rows = evidence_rows(f)
    by_tier = {"fact": [], "checked": [], "judgement": []}
    for t, m, txt in rows:
        by_tier[t].append((m, txt))
    parts = ['<section class="sec"><h3>Evidence</h3>']
    tier_labels = [("fact", "Fact", "true with no model"),
                   ("checked", "Checked", "verified against GitHub"),
                   ("judgement", "Judgement", "model opinion, unverified")]
    for key, label, sub in tier_labels:
        items = by_tier[key]
        if not items:
            continue
        parts.append(f'<div class="tier-block tier-{key}"><h4>{label}'
                     f'<span class="tier-sub">{sub}</span></h4><ul class="tier-list">')
        parts.extend(f'<li>{m}<span class="mktxt">{txt}</span></li>' for m, txt in items)
        parts.append('</ul></div>')
    parts.append('</section>')
    return "".join(parts)


def verdict_section_html(r):
    v = r["verdict"]
    bucket = v.get("bucket") or 0
    name, note = BUCKET_META[bucket]
    reason = esc(v.get("reason") or "no reason recorded.")
    return f'''<section class="sec"><h3>Verdict</h3>
<p class="verdict-name">{esc(name)}</p>
<p class="verdict-reason">{reason}</p></section>'''


QUALITY_CLASS = {"solid": "q-ok", "workable": "q-mid",
                 "needs work": "q-low", "cannot tell": "q-unk"}


def review_section_html(r):
    rev = r.get("review")
    if not rev:
        return '''<section class="sec"><h3>Code review</h3>
<p class="empty">Not run in a full-queue pass.</p></section>'''
    q = rev.get("quality") or "unclear"
    bits = [f'<section class="sec"><h3>Code review</h3>'
            f'<p class="review-tag">Opinion, not a checked fact: <b>{esc(q)}</b></p>']
    if rev.get("headline"):
        bits.append(f'<p class="review-head">{esc(rev["headline"])}</p>')
    if rev.get("blocking"):
        bits.append('<div class="rl"><span class="rk block">Blocking</span><ul>'
                    + "".join(f"<li>{esc(b)}</li>" for b in rev["blocking"]) + "</ul></div>")
    if rev.get("strengths"):
        bits.append('<div class="rl"><span class="rk">Does well</span><ul>'
                    + "".join(f"<li>{esc(x)}</li>" for x in rev["strengths"]) + "</ul></div>")
    if rev.get("improvements"):
        items = []
        for i in rev["improvements"]:
            where = f' <code>{esc(i["where"])}</code>' if i.get("where") else ""
            why = f', {esc(i["why"])}' if i.get("why") else ""
            items.append(f'<li>{esc(i.get("what", ""))}{where}{why}</li>')
        bits.append('<div class="rl"><span class="rk">Could improve</span><ul>' + "".join(items) + "</ul></div>")
    if rev.get("risk"):
        bits.append(f'<p class="review-risk">If wrong: {esc(rev["risk"])}</p>')
    bits.append("</section>")
    return "".join(bits)


def memory_section_html(r):
    if r.get("is_new"):
        body = "New since your last visit."
    elif (r.get("times_seen") or 0) > 1:
        body = f'Visit {r["times_seen"]}, first seen {esc(r.get("first_seen") or "unknown")}.'
    else:
        body = "First visit, no prior run to compare."
    return f'<section class="sec"><h3>Memory</h3><p>{body}</p></section>'


def link_section_html(r, repo):
    n = r["input"]["number"]
    url = f"https://github.com/{repo}/pull/{n}"
    return f'''<section class="sec sec-link"><h3>Link out</h3>
<a class="gh-link" href="{esc(url)}" target="_blank" rel="noopener">Open #{n} on GitHub &#8594;</a></section>'''


def title_html(r):
    flag = ""
    f = r["facts"]
    bucket = r["verdict"].get("bucket") or 0
    if is_strong(f) and bucket == 3:
        flag = '<div class="pflag">Stronger evidence than this pile implies.</div>'
    ci = r["input"]
    return f'''<div class="page-title-block">
  <span class="page-num">#{ci["number"]}</span>
  <h1 class="page-title">{esc(ci["title"])}</h1>
  {flag}
</div>'''


def page_html(r, repo, sha8):
    ci = r["input"]
    pid = anchor_id(ci["number"])
    body = f'''{title_html(r)}
<div class="page-2col">
  <div class="page-main">
    {verdict_section_html(r)}
    {evidence_section_html(r)}
    {review_section_html(r)}
    {memory_section_html(r)}
  </div>
  <aside class="page-side">
    <h3 class="props-h">Properties</h3>
    {properties_html(r, sha8)}
    {link_section_html(r, repo)}
  </aside>
</div>'''
    return f'''<article class="page swap" id="{pid}" data-num="{ci["number"]}" hidden>
  <button class="back" data-action="back" aria-label="Back to board">&#8592; back to board</button>
  {body}
</article>'''


# The single surface: warm paper ground, three distinct planes (recessed tray,
# raised card, floating panel) so depth reads as structure rather than
# decoration. One accent, no red, sentence case, no legend: the tier labels
# and the per-row plain-English sentence are the only carriers of meaning.
CSS = '''
:root{
  --paper:#f8f5ee;
  --ink:#18140f;
  --muted:#635a4d;
  --line:#e1d9ca;
  --accent:#8a5f10;
  --accent-soft:#f1e6ce;

  /* morphism surfaces: three distinct planes, not one flat sheet */
  --tray:#ede4d1;           /* recessed: the board column slot cards sit in */
  --tray-shadow:inset 0 2px 5px rgba(24,20,15,.10), inset 0 -1px 0 rgba(255,255,255,.55);
  --card-surface:#fffdf8;    /* raised: individual cards */
  --card-shadow:0 1px 2px rgba(24,20,15,.05), 0 6px 16px rgba(24,20,15,.06);
  --card-shadow-hover:0 2px 4px rgba(24,20,15,.07), 0 10px 24px rgba(24,20,15,.10);
  --panel-surface:#f2ece0;   /* raised: sidebar / evidence panel */
  --panel-shadow:0 1px 2px rgba(24,20,15,.04), 0 10px 26px rgba(24,20,15,.07);

  --dur-snappy:220ms; --ease-snappy:cubic-bezier(.175,.885,.32,1.1);
  --dur-smooth:300ms; --ease-smooth:cubic-bezier(.19,1,.22,1);
}
*{box-sizing:border-box}
html{background:var(--paper)}
body{margin:0;background:var(--paper);color:var(--ink);
  font:400 15px/1.6 ui-monospace,"JetBrains Mono","SF Mono",Menlo,Consolas,monospace;
  -webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:0 28px}
h1,h2,h3,h4{font-family:inherit;margin:0;font-weight:600;letter-spacing:-.01em}
a{color:inherit}
button{font:inherit}

/* --- marks: fact square / checked diamond / judgement circle, 15px, shape+fill carries meaning --- */
.mk{display:inline-block;width:15px;height:15px;flex:0 0 auto;vertical-align:-3px}
.mk-fact{background:var(--muted);border-radius:2px}
.mk-checked{background:var(--ink);transform:rotate(45deg);border-radius:2px;position:relative}
.mk-checked.mk-hollow{background:transparent;border:2px solid var(--ink)}
.mk-checked.mk-dashed{background:transparent;border:2px dashed var(--ink)}
.mk-checked.mk-crossed{background:transparent;border:2px solid var(--ink)}
.mk-checked.mk-crossed::after{content:"";position:absolute;left:50%;top:50%;width:19px;height:2.4px;
  background:var(--ink);transform:translate(-50%,-50%) rotate(45deg)}
.mk-judge{width:15px;height:15px;border-radius:50%;background:transparent;border:2px solid var(--ink);opacity:.8}
/* nothing was verified: a neutral placeholder, never the filled "confirmed" diamond */
.chip-checked .mk.mk-empty{width:15px;height:15px;border-radius:1px;background:transparent;border:1.5px dotted var(--muted);transform:none}
/* compound selector: real specificity, so this beats .chip-checked's own
   background regardless of source order (a plain .chip-empty tied at equal
   specificity is inert and was caught rendering byte-identical to a filled
   chip) */
.chip-checked.chip-empty{background:var(--paper);color:var(--muted)}

.mk-judge.mk-j-nomatch{background:var(--ink);opacity:1}
.mk-judge.mk-j-unclear{border-style:dashed}
.mktxt{margin-left:9px}

/* --- board: recessed tray holds raised cards, so depth reads as structure --- */
.board-head{padding:30px 0 18px;border-bottom:1px solid var(--line)}
.board-head h1{font-size:20px}
.board-sub{margin:8px 0 0;color:var(--muted);font-size:13.5px}
.board-sub code{background:var(--accent-soft);padding:1px 5px;border-radius:3px}

/* --- one aggregate per run, read before any card --- */
.strip{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
  gap:10px;margin:20px 0 4px}
.strip .cell{background:var(--card-surface);box-shadow:var(--card-shadow);
  border-radius:10px;padding:14px 16px}
.strip .cell .n{font:650 26px/1 inherit;letter-spacing:-.02em}
.strip .cell .lab{margin-top:5px;font-weight:600;font-size:13px}
.strip .cell .sub{margin-top:2px;color:var(--muted);font-size:12px}

.board-cols{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin:22px 0 0}
.col{background:var(--tray);box-shadow:var(--tray-shadow);border-radius:12px;padding:18px 16px 22px;min-width:0}
.col-head{display:flex;align-items:center;justify-content:space-between;gap:10px}
.col-head h2{font-size:14px}
.col-head .count{font-size:13px;color:var(--muted);background:var(--card-surface);box-shadow:var(--card-shadow);
  border-radius:999px;padding:1px 9px}
.col-note{margin:6px 0 16px;color:var(--muted);font-size:12.5px;line-height:1.5}
.col-cards{display:grid;gap:10px}
.card{all:unset;display:block;background:var(--card-surface);box-shadow:var(--card-shadow);border-radius:10px;
  padding:13px 14px;cursor:pointer;transition:transform var(--dur-snappy) var(--ease-snappy),
  box-shadow var(--dur-snappy) var(--ease-snappy)}
.card:hover,.card:focus-visible{transform:translateY(-2px);box-shadow:var(--card-shadow-hover)}
.card:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.card:active{transform:translateY(0)}
.card-top{display:flex;justify-content:space-between;gap:8px;align-items:baseline}
.card .num{font-size:12.5px;color:var(--muted)}
.card .rank{font-size:11.5px;color:var(--muted)}
.card-title{margin-top:6px;font-size:14.5px;font-weight:600;line-height:1.4}
.card-evidence{margin-top:11px;display:flex;gap:8px;flex-wrap:wrap}

/* --- later-today split inside a column, same shape as the flat report's <details> --- */
.col-more{margin-top:10px}
.col-more summary{cursor:pointer;color:var(--muted);font-size:12px;padding:6px 2px;list-style:revert}
.col-more summary:hover{color:var(--ink)}
.col-more .col-cards{margin-top:10px}

/* labelled chips: each tier is its own small surface, not just a coloured dot */
.chip{display:inline-flex;align-items:center;gap:6px;font-size:12px;padding:3px 8px 3px 6px;border-radius:6px;
  color:var(--muted)}
.chip .mk{width:10px;height:10px}
.chip-fact{background:var(--paper)}
.chip-checked{background:var(--accent-soft);color:#5b3f0a}
.chip-checked .mk{background:var(--accent);border-color:var(--accent)}
.chip-checked .mk.mk-crossed::after{background:var(--accent)}
/* ponytail: font-weight is the only channel this ships with today for the
   highest-severity finding (an invented citation). No PR in the shipped
   dataset has a mixed checked state, so this path is unexercised; strengthen
   with shape or border once a real one does. */
.chip-flag{font-weight:700}
.chip-judge{background:transparent;border:1px solid var(--line)}
.chip-judge .mk{border-color:var(--muted)}
.cflag{margin-top:9px;font-size:12px;color:var(--accent);border-top:1px dashed var(--line);padding-top:8px}
.board-foot{margin:26px 0 60px;color:var(--muted);font-size:12.5px;border-top:1px solid var(--line);padding-top:16px}

/* --- page --- */
.page{padding:28px 0 80px}
.back{all:unset;display:inline-flex;align-items:center;gap:8px;cursor:pointer;color:var(--ink);
  font-size:13.5px;font-weight:600;padding:7px 4px;margin-bottom:22px;
  transition:transform var(--dur-snappy) var(--ease-snappy),color var(--dur-snappy) var(--ease-snappy)}
.back:hover,.back:focus-visible{color:var(--accent);transform:translateX(-3px)}
.back:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:4px}
.page-title-block{margin-bottom:26px}
.page-num{font-size:13px;color:var(--muted)}
.page-title{font-size:26px;line-height:1.3;margin-top:6px;letter-spacing:-.015em}
.pflag{margin-top:12px;padding:10px 13px;background:var(--accent-soft);border-radius:8px;font-size:13.5px;color:#5b3f0a}
.props-h{font-size:12px;letter-spacing:.03em;color:var(--muted);margin-bottom:8px}
.props{display:grid;gap:0;border-top:1px solid var(--line)}
.prop-row{display:grid;grid-template-columns:100px 1fr;gap:14px;padding:9px 0;border-bottom:1px solid var(--line);
  line-height:1.6}
.prop-k{color:var(--muted);font-size:12.5px}
.prop-v{font-size:13px}
.prop-v code{background:var(--accent-soft);padding:1px 5px;border-radius:3px}
.sec{margin-top:32px}
.sec h3{font-size:13px;letter-spacing:.03em;color:var(--muted);margin-bottom:12px}
.verdict-name{font-size:16.5px;font-weight:650;margin:0 0 6px}
.verdict-reason{font-size:15px;max-width:74ch;line-height:1.65}
.tier-block{margin-bottom:14px;padding:14px 16px;border-radius:10px}
.tier-fact{background:var(--paper);box-shadow:var(--tray-shadow)}
.tier-checked{background:var(--panel-surface);box-shadow:var(--panel-shadow)}
.tier-judgement{background:transparent;border:1px solid var(--line)}
.tier-block h4{font-size:12.5px;color:var(--ink);font-weight:700;margin-bottom:10px;letter-spacing:.01em;
  display:flex;align-items:baseline;gap:8px}
.tier-sub{font-weight:400;color:var(--muted);font-size:11.5px}
.tier-list{list-style:none;margin:0;padding:0;display:grid;gap:9px}
.tier-list li{display:flex;align-items:flex-start;gap:0;font-size:14px;line-height:1.55;max-width:76ch}
.tier-list .mk{margin-top:3px}
.empty{color:var(--muted);font-size:14px}
.review-tag{font-size:13.5px;color:var(--muted)}
.review-head{font-size:16px;font-weight:600;margin:8px 0 0}
.rl{margin-top:14px}
.rk{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.04em;
  color:var(--ink);background:var(--panel-surface);box-shadow:var(--panel-shadow);border-radius:5px;
  padding:2px 8px;margin-bottom:7px}
.rl ul{margin:0;padding-left:18px}
.rl li{margin:4px 0;font-size:14px}
.review-risk{margin-top:14px;font-size:13.5px;color:#5b3f0a;background:var(--accent-soft);
  padding:9px 12px;border-radius:6px;display:inline-block}
.gh-link{display:inline-flex;align-items:center;gap:8px;font-size:14px;font-weight:600;color:var(--ink);
  background:var(--card-surface);box-shadow:var(--card-shadow);border-radius:8px;padding:9px 14px;text-decoration:none;
  transition:box-shadow var(--dur-snappy) var(--ease-snappy),transform var(--dur-snappy) var(--ease-snappy)}
.gh-link:hover,.gh-link:focus-visible{box-shadow:var(--card-shadow-hover);transform:translateY(-1px)}
.gh-link:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

/* --- two-column page: sidebar reads as its own panel, not a bordered strip --- */
.page-2col{display:grid;grid-template-columns:1fr 300px;gap:32px;align-items:start}
.page-side{position:sticky;top:24px;background:var(--panel-surface);box-shadow:var(--panel-shadow);
  border-radius:14px;padding:20px}
.page-side .sec{margin-top:22px}
.page-side .sec:first-child{margin-top:0}
.page-side .sec-link .gh-link{width:100%;justify-content:center}

/* --- view swap --- */
.swap{opacity:0;transform:translateY(6px);
  transition:opacity var(--dur-smooth) var(--ease-smooth),transform var(--dur-smooth) var(--ease-smooth)}
.swap[hidden]{display:none}
.swap.in{opacity:1;transform:translateY(0)}
@media (prefers-reduced-motion:reduce){
  .card,.back,.swap{transition:none!important}
}
@media (max-width:900px){
  .board-cols{grid-template-columns:1fr}
  .page-2col{grid-template-columns:1fr}
  .page-side{position:static}
}
'''

JS = '''
(function(){
  var board = document.getElementById("view-board");
  var pages = document.querySelectorAll(".page");
  var lastFocus = null;
  function reveal(el){
    el.hidden = false;
    el.classList.remove("in");
    void el.offsetWidth;
    el.classList.add("in");
  }
  function showBoard(){
    pages.forEach(function(p){ p.hidden = true; p.classList.remove("in"); });
    reveal(board);
    if(lastFocus){ lastFocus.focus(); }
  }
  function openPage(num){
    var target = document.getElementById("pr-" + num);
    if(!target) return;
    lastFocus = document.querySelector('.card[data-target="pr-' + num + '"]');
    board.hidden = true;
    board.classList.remove("in");
    pages.forEach(function(p){ p.hidden = (p !== target); if(p !== target) p.classList.remove("in"); });
    reveal(target);
    target.querySelector(".back").focus();
    window.scrollTo(0,0);
  }
  document.addEventListener("click", function(e){
    var card = e.target.closest(".card");
    if(card){ openPage(card.dataset.target.replace("pr-","")); return; }
    var back = e.target.closest("[data-action=back]");
    if(back){ showBoard(); return; }
  });
  document.addEventListener("keydown", function(e){
    if(e.key === "Escape" && board.hidden){ showBoard(); }
  });
})();
'''


def write(data, path):
    repo = data["repo"]
    rs = data["results"]
    has_mem = bool(data.get("prior_runs"))
    sha8 = data["sha"][:8]
    board = board_html(data, rs, has_mem)
    pages = "\n".join(page_html(r, repo, sha8) for r in rs)
    out = f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(repo)} triage, kanban</title>
<style>{CSS}</style></head>
<body>
<div class="wrap">
  <div class="swap in" id="view-board">
    {board}
  </div>
  {pages}
</div>
<script>{JS}</script>
</body></html>'''
    open(path, "w").write(out)
    return path


if __name__ == "__main__":
    import sys
    src = sys.argv[1]
    data = json.load(open(src))
    print(write(data, src.replace(".json", ".html")))
