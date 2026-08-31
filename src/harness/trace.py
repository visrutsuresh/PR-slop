"""Trajectory logger for micro1 Agentic Workflows Hackathon submissions.

ponytail: single-purpose module, no framework, no plugin system. If judges
ever need step-level capture provenance (some steps raw, others hand-typed
within one run) the upgrade path is a `capture` kwarg on Trace.step(), not
a wider constructor or a second class.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

# Anchored to the module location, not the process cwd: a run launched from
# a subdirectory must still land in the one traces dir render_index() reads.
TRACE_DIR = Path(__file__).resolve().parent.parent.parent / "traces"
MAX_FIELD_CHARS = 4000

_HOME = os.path.expanduser("~")

# Common API-key / bearer-token shapes, PLUS a few structural patterns
# (JWT, PEM block) and an in-string key=value / key: value rule. This is
# NOT exhaustive: it covers the credential shapes actually seen in tool
# output during this build (bare and embedded JWTs, PEM private blocks,
# Stripe/HuggingFace prefixes, any KEY=value or "key": "value" pair whose
# key name matches _SECRET_KEY_NAMES, and scheme://user:password@host
# connection strings). The key-name check below only
# fires when the key is a real dict key; it does NOT catch a secret sitting
# inside an unstructured string blob with no key at all (e.g. a raw log
# line with no recognizable prefix or key name). Redaction is defense in
# depth, not a guarantee: never assume it catches everything, review traces
# before they leave the machine.
_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{10,}"),
    re.compile(r"sk_live_[A-Za-z0-9]{16,}"),  # Stripe live secret key
    re.compile(r"hf_[A-Za-z0-9]{20,}"),  # HuggingFace token
    re.compile(r"\b[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),  # JWT (3 dot-segments)
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),  # PEM block
]
# In-string key=value / key: value rule, run separately so the key name is
# preserved and only the value is masked (e.g. PASSWORD=hunter2 -> PASSWORD=[REDACTED]).
# No \b around the key name: real key names are commonly compound
# (aws_secret_access_key, SECRET_TOKEN) where underscores keep the whole
# thing one \w-run, so \b would never fire inside it.
_SECRET_KV_PATTERN = re.compile(
    r"(?i)([\w.-]*(?:api[_-]?key|secret|token|password)[\w.-]*)(\s*[:=]\s*)(\S+)"
)
# Connection-URL credential rule: scheme://user:password@host (postgres,
# mongodb+srv, redis, mysql, amqp, ...). Masks only the password so the
# scheme, user and host stay readable for debugging. User may be empty
# (redis's `redis://:password@host` shape), handled by `*` not `+`.
_CONN_URL_PATTERN = re.compile(r"([a-zA-Z][a-zA-Z0-9+.-]*://[^:/@\s]*:)([^@\s]+)(@)")
_SECRET_KEY_NAMES = re.compile(r"(api[_-]?key|token|secret|password)", re.IGNORECASE)


def _redact_str(s: str) -> str:
    for pat in _SECRET_PATTERNS:
        s = pat.sub("[REDACTED]", s)
    s = _SECRET_KV_PATTERN.sub(lambda m: f"{m.group(1)}{m.group(2)}[REDACTED]", s)
    s = _CONN_URL_PATTERN.sub(lambda m: f"{m.group(1)}[REDACTED]{m.group(3)}", s)
    s = s.replace(_HOME, "~")
    if len(s) > MAX_FIELD_CHARS:
        cut = len(s) - MAX_FIELD_CHARS
        s = s[:MAX_FIELD_CHARS] + f"...[TRUNCATED {cut} chars]"
    return s


def redact(value: Any, key: str | None = None) -> Any:
    """Recursive redaction pass. Runs before every disk write, no exceptions."""
    if isinstance(value, str):
        if key and _SECRET_KEY_NAMES.search(key):
            return "[REDACTED]"
        return _redact_str(value)
    if isinstance(value, dict):
        return {k: redact(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


class Trace:
    """Records one agent run as it happens. Usable as a context manager.

        with Trace("coder", "fix the bug") as t:
            t.step("read the file", tool="read", args={"path": "x.py"}, response="...")
            t.result = {"status": "ok", "outcome": "fixed"}

    `result` is a plain attribute, not a method, so the clean-exit path can
    set it any time before the block ends. On exception, __exit__ fills it
    in from the exception itself so the terminal record is never missing.
    """

    def __init__(self, agent: str, instruction: str, capture: str = "reconstructed"):
        assert capture in ("captured", "reconstructed")
        self.agent = agent
        self.instruction = instruction
        self.capture = capture
        self.run_id = f"{agent}-{int(time.time() * 1000)}"
        self.result: dict | None = None
        self._steps: list[dict] = []
        self._start = time.time()
        TRACE_DIR.mkdir(exist_ok=True)
        self._path = TRACE_DIR / f"{self.run_id}.jsonl"
        self._write({
            "type": "meta",
            "run_id": self.run_id,
            "agent": self.agent,
            "instruction": self.instruction,
            "capture": self.capture,
            "started_at": _iso(self._start),
        })

    def _write(self, record: dict) -> None:
        clean = redact(record)
        with self._path.open("a") as f:
            f.write(json.dumps(clean, default=str) + "\n")

    def step(self, action: str, tool: str | None = None, args: Any = None,
              response: Any = None, retry: Any = None, checkpoint: Any = None,
              tokens: int | None = None, cost: float | None = None) -> None:
        now = time.time()
        record = {
            "type": "step",
            "step": len(self._steps),
            "ts": _iso(now),
            "elapsed_s": round(now - self._start, 3),
            "action": action,
            "tool": tool,
            "args": args,
            "response": response,
            "retry": retry,
            "checkpoint": checkpoint,
            "tokens": tokens,
            "cost": cost,
        }
        self._steps.append(record)
        self._write(record)

    def __enter__(self) -> "Trace":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        now = time.time()
        if exc_type is not None:
            self.result = {"status": "error", "outcome": f"{exc_type.__name__}: {exc_val}"}
        elif self.result is None:
            self.result = {"status": "unknown", "outcome": None}
        self._write({
            "type": "result",
            "ended_at": _iso(now),
            "elapsed_total_s": round(now - self._start, 3),
            "result": self.result,
        })
        return False


def _iso(ts: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


def _read_records(run_id: str) -> list[dict]:
    """A run interrupted mid-write (Ctrl-C, OOM, laptop sleep) leaves a
    truncated final line. Skip it rather than raise: one bad line must not
    cost the whole trajectory, and render_index() must still cover every
    other agent's runs."""
    path = TRACE_DIR / f"{run_id}.jsonl"
    records = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"[trace] skipping malformed line in {path.name}")
    return records


def _fence_for(text: str) -> str:
    """Backtick fence one char longer than the longest run of backticks in
    text, so the fence can never be terminated early by its own content."""
    longest = run = 0
    for ch in text:
        run = run + 1 if ch == "`" else 0
        longest = max(longest, run)
    return "`" * max(3, longest + 1)


def _render_field(label: str, value: Any) -> list[str]:
    """Multi-line or backtick-bearing values get a fenced block (CommonMark
    preserves newlines inside a fence); short single-line values stay an
    inline code span."""
    text = str(value)
    if "\n" in text or "`" in text:
        fence = _fence_for(text)
        return [f"- **{label}:**", fence, text, fence, ""]
    return [f"- **{label}:** `{text}`"]


def render_markdown(run_id: str) -> str:
    """Render one trace to readable markdown. Reads back the already-redacted
    JSONL rather than any in-memory copy, so a rendered trace structurally
    cannot leak anything the redaction pass already stripped."""
    records = _read_records(run_id)
    meta = next(r for r in records if r["type"] == "meta")
    steps = [r for r in records if r["type"] == "step"]
    result = next((r for r in records if r["type"] == "result"), None)

    lines = [
        f"# Trace: {meta['agent']} ({run_id})",
        "",
        f"**Instruction:** {meta['instruction']}",
        f"**Capture:** {meta['capture']}",
        f"**Started:** {meta['started_at']}",
        "",
        "## Steps",
        "",
    ]
    for s in steps:
        lines.append(f"### Step {s['step']} — {s['ts']} (+{s['elapsed_s']}s)")
        lines.append(f"- **Action:** {s['action']}")
        if s.get("tool"):
            lines.append(f"- **Tool:** `{s['tool']}`")
        if s.get("args") is not None:
            lines.extend(_render_field("Args", s["args"]))
        if s.get("response") is not None:
            lines.extend(_render_field("Response", s["response"]))
        if s.get("retry") is not None:
            lines.append(f"- **Retry of:** {s['retry']}")
        if s.get("checkpoint") is not None:
            lines.append(f"- **Human checkpoint:** {s['checkpoint']}")
        lines.append("")

    lines.append("## Result")
    if result:
        r = result["result"] or {}
        lines.append(f"- **Status:** {r.get('status')}")
        lines.append(f"- **Outcome:** {r.get('outcome')}")
        lines.append(f"- **Ended:** {result['ended_at']} (total {result['elapsed_total_s']}s)")
    else:
        lines.append("- (no terminal result recorded)")

    md = "\n".join(lines) + "\n"
    (TRACE_DIR / f"{run_id}.md").write_text(md)
    return md


def render_index() -> str:
    """List every agent used with a link to its trace file(s)."""
    TRACE_DIR.mkdir(exist_ok=True)
    by_agent: dict[str, list[str]] = {}
    for jf in sorted(TRACE_DIR.glob("*.jsonl")):
        run_id = jf.stem
        try:
            records = _read_records(run_id)
            meta = next((r for r in records if r["type"] == "meta"), None)
            if not meta:
                continue
            render_markdown(run_id)
            by_agent.setdefault(meta["agent"], []).append(run_id)
        except Exception as e:
            # One unreadable file must never take out every other agent's
            # index entry: report it and move on.
            print(f"[trace] skipping {jf.name}: {e}")
            continue

    lines = ["# Trace Index", ""]
    for agent, run_ids in sorted(by_agent.items()):
        lines.append(f"## {agent}")
        for run_id in run_ids:
            lines.append(f"- [{run_id}]({run_id}.md)")
        lines.append("")
    md = "\n".join(lines) + "\n"
    (TRACE_DIR / "INDEX.md").write_text(md)
    return md
