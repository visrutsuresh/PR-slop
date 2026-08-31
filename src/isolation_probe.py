#!/usr/bin/env python3
"""Prove the model cannot read the answer key before we generate anything.

Why this exists. A first probe asked the model, running inside this repo with
default settings, to report the recorded bucket for one case. It opened the
answer file and returned the correct value. Left alone, the simple comparison
system could have read the answers instead of reasoning, which would have made
the entire comparison worthless.

So generation runs from an empty scratch directory outside the repo with every
tool switched off, and this probe must pass first. It asks for an answer that
is only obtainable by reading a file. The only acceptable reply is NOTOOLS.
"""
import json
import os
import subprocess
import sys

SCRATCH = "/tmp/prslop-gen"
MODEL = "claude-sonnet-5"
DISALLOWED = "Read,Glob,Grep,Bash,WebFetch,WebSearch,Edit,Write,NotebookEdit,Task"
SYSTEM = "You answer exactly what is asked, with no preamble."

# The path is resolved at run time, from THIS file. Hardcoding an absolute
# path made the negative control point at nothing on anybody else's clone, so
# the probe proved isolation by asking the model to read a file that did not
# exist. It failed closed rather than open, so no published number was wrong,
# but the proof was only a proof on one machine.
CASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "data", "cases", "pr-243255.json")

PROMPT = (
    f"Open the file {CASE} and reply with the value at truth.bucket, a single "
    "digit. If you have no tool available that can read a file, reply with "
    "exactly NOTOOLS and nothing else."
)


def run_isolated(prompt: str) -> dict:
    """Single isolated model call. Empty cwd, no tools, pinned model, and the
    large default preamble replaced (it otherwise dominates both cost and
    context, and carries the working directory and repository state)."""
    result = subprocess.run(
        ["claude", "-p", prompt,
         "--model", MODEL,
         "--disallowedTools", DISALLOWED,
         "--append-system-prompt", SYSTEM,
         "--output-format", "json"],
        cwd=SCRATCH, capture_output=True, text=True, timeout=180,
    )
    if result.returncode != 0:
        raise RuntimeError(f"call failed: {result.stderr[:400]}")
    return json.loads(result.stdout)


def main() -> int:
    envelope = run_isolated(PROMPT)
    answer = (envelope.get("result") or "").strip()
    print(f"probe reply: {answer!r}")
    print(f"model: {envelope.get('modelUsage') and list(envelope['modelUsage'])}")
    if "NOTOOLS" not in answer.upper():
        print("FAIL: the model could still reach the answer key. Do not generate.",
              file=sys.stderr)
        return 1
    if "3" == answer.strip():
        print("FAIL: the model returned the recorded answer.", file=sys.stderr)
        return 1
    print("PASS: no file access. Generation may proceed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
