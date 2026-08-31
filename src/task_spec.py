#!/usr/bin/env python3
"""The task description, shared WORD FOR WORD by the simple comparison system
and by our own system.

This lives in one file on purpose. If the two sides were given different
wording, the measured difference would partly reflect how hard we tried on the
prompt rather than what the systems can actually do. The README pastes this
text verbatim so a judge can check both sides received it.
"""

BUCKET_DEFINITIONS = """\
You are triaging a pull request for a busy open source maintainer.

Sort it into exactly one of three buckets:

  1 = act now.          Work worth merging, and it addresses a problem someone
                        had already reported in the project.
  2 = worth reviewing.  A genuine contribution that needs a human read, with no
                        indication it answers an already-reported problem.
  3 = not merged.       You judge the maintainer would not merge this. Note this
                        covers several different things: routine automated
                        housekeeping, work superseded by another approach, a
                        duplicate, or low-effort or machine-generated filler.

Bucket 3 is NOT a quality verdict on the contributor. It means you judge this
did not become part of the codebase.

You may also answer 0 = cannot determine, if the evidence does not support a
call. Answering 0 is preferred over guessing.
"""

OUTPUT_CONTRACT = """\
Reply with JSON only, no prose around it, in exactly this shape:

{"bucket": 1|2|3|0,
 "confidence": "high"|"medium"|"low",
 "reason": "one or two sentences",
 "citations": ["#12345", "src/path/to/file.ts"]}

Rules for "citations":
  - Cite only things you can actually point at: issue numbers as #NNNNN, or
    file paths.
  - If you have no way to check the repository, return an EMPTY list. Do not
    invent an issue number or a file path to fill the field. An empty list is
    a correct answer and is scored as such.
"""


def build_case_prompt(case_input: dict) -> str:
    files = case_input.get("changed_files") or []
    file_list = "\n".join(f"  {p}" for p in files[:60])
    if len(files) > 60:
        file_list += f"\n  ...and {len(files) - 60} more"
    patch = case_input.get("patch") or ""
    if len(patch) > 24000:
        patch = patch[:24000] + "\n...[patch truncated for length]"
    return (
        f"{BUCKET_DEFINITIONS}\n"
        f"{OUTPUT_CONTRACT}\n"
        f"--- pull request ---\n"
        f"title: {case_input.get('title')}\n\n"
        f"description:\n{case_input.get('body') or '(none)'}\n\n"
        f"files changed ({len(files)}):\n{file_list or '  (none listed)'}\n\n"
        f"code changes:\n{patch}\n"
    )
