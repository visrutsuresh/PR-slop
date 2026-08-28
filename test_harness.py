"""ponytail: one runnable check, plain asserts, no framework.
Run: python3 test_harness.py

This test suite NEVER touches the real traces/ directory. It repoints
trace.TRACE_DIR at a throwaway directory it owns before any test runs, and
only that directory is ever rmtree'd. Real submission trajectories in
traces/ must survive `python3 test_harness.py` / `./run.sh eval` untouched.
"""
import json
import shutil
from pathlib import Path

import harness.trace as trace

_TEST_TRACE_DIR = Path(__file__).resolve().parent / "traces_test"
shutil.rmtree(_TEST_TRACE_DIR, ignore_errors=True)
trace.TRACE_DIR = _TEST_TRACE_DIR


def test_round_trip_and_terminal_result_on_clean_exit():
    with trace.Trace("tester-agent", "say hello") as t:
        t.step("greeted", tool="echo", args={"msg": "hi"}, response={"ok": True})
        t.result = {"status": "ok", "outcome": "greeted successfully"}
    records = trace._read_records(t.run_id)
    assert records[0]["type"] == "meta"
    assert records[-1]["type"] == "result"
    assert records[-1]["result"]["status"] == "ok"
    steps = [r for r in records if r["type"] == "step"]
    assert len(steps) == 1
    md = trace.render_markdown(t.run_id)
    assert "greeted successfully" in md
    assert "Step 0" in md


def test_terminal_result_written_on_exception():
    run_id = None
    try:
        with trace.Trace("crash-agent", "will fail") as t:
            run_id = t.run_id
            t.step("about to crash")
            raise ValueError("boom")
    except ValueError:
        pass
    records = trace._read_records(run_id)
    result_record = records[-1]
    assert result_record["type"] == "result"
    assert result_record["result"]["status"] == "error"
    assert "boom" in result_record["result"]["outcome"]


def test_jsonl_is_one_valid_json_object_per_line():
    with trace.Trace("agent-a", "do things") as t:
        t.step("step one")
        t.step("step two")
        t.result = {"status": "ok", "outcome": "done"}
    path = trace.TRACE_DIR / f"{t.run_id}.jsonl"
    lines = path.read_text().strip().split("\n")
    assert len(lines) == 4  # meta + 2 steps + result
    for line in lines:
        json.loads(line)  # raises ValueError if any line is not valid JSON


def test_render_index_lists_every_agent():
    for agent in ("agent-a", "agent-b"):
        with trace.Trace(agent, f"{agent} instruction") as t:
            t.step("did a thing")
            t.result = {"status": "ok", "outcome": "fine"}
    md = trace.render_index()
    assert "agent-a" in md
    assert "agent-b" in md
    assert (trace.TRACE_DIR / "INDEX.md").exists()


def test_planted_secret_redacted_from_jsonl_and_rendered_markdown():
    fake_bearer = "Bearer abcdefghijklmnopqrstuvwxyz123456"
    home_marker = trace._HOME
    with trace.Trace("secret-agent", "call an api") as t:
        t.step(
            "called the api",
            tool="http_post",
            args={"api_key": "supersecretvalue123", "path": f"{home_marker}/project/creds"},
            response={"auth_header": fake_bearer},
        )
        t.result = {"status": "ok", "outcome": "done"}

    jsonl_text = (trace.TRACE_DIR / f"{t.run_id}.jsonl").read_text()
    assert "supersecretvalue123" not in jsonl_text
    assert fake_bearer not in jsonl_text
    assert home_marker not in jsonl_text

    md = trace.render_markdown(t.run_id)
    assert "supersecretvalue123" not in md
    assert fake_bearer not in md
    assert home_marker not in md


def test_string_blob_secret_shapes_redacted():
    # Keyless-blob shapes the key-name check alone cannot catch: exercises
    # the string-level rules added for objection #3 (JWT, PEM block, Stripe
    # / HuggingFace prefixes, in-string key=value / key: value pairs) plus
    # scheme://user:password@host connection URLs (incl. redis's empty-user
    # `redis://:password@host` shape).
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    jwt_in_json = '{"access_token": "%s", "type": "bearer"}' % jwt
    pem = "-----BEGIN RSA PRIVATE KEY-----\nMIIBOgIBAAJBAK...fakekeydata...\n-----END RSA PRIVATE KEY-----"
    stripe = "sk_live_51ABCDEFGHIJKLMNOPQRSTUV"
    hf = "hf_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"
    kv_password = "PASSWORD=hunter2plaintext"
    kv_secret_colon = 'aws_secret_access_key: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"'
    pg_url = "postgres://user:hunter2@db.internal:5432/prod"
    mongo_url = "mongodb+srv://admin:p4ssw0rd@cluster0.mongodb.net/db"
    redis_url = "redis://:mysecret@127.0.0.1:6379/0"

    with trace.Trace("secret-blob-agent", "call an api") as t:
        t.step("bare jwt", tool="http_get", args=None, response=jwt)
        t.step("jwt in json body", tool="http_post", args=None, response=jwt_in_json)
        t.step("pem block", tool="read_file", args=None, response=pem)
        t.step("stripe key", tool="env_dump", args=None, response=stripe)
        t.step("hf token", tool="env_dump", args=None, response=hf)
        t.step("kv password", tool="env_dump", args=None, response=kv_password)
        t.step("kv secret colon", tool="env_dump", args=None, response=kv_secret_colon)
        t.step("postgres url", tool="env_dump", args=None, response=pg_url)
        t.step("mongodb url", tool="env_dump", args=None, response=mongo_url)
        t.step("redis url", tool="env_dump", args=None, response=redis_url)
        t.result = {"status": "ok", "outcome": "done"}

    secrets = (jwt, "fakekeydata", stripe, hf, "hunter2plaintext",
               "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
               "hunter2", "p4ssw0rd", "mysecret")
    jsonl_text = (trace.TRACE_DIR / f"{t.run_id}.jsonl").read_text()
    for secret in secrets:
        assert secret not in jsonl_text, f"leaked: {secret!r}"
    # scheme, user and host must survive so the trace stays readable
    for readable in ("postgres://user:", "@db.internal:5432/prod",
                      "mongodb+srv://admin:", "@cluster0.mongodb.net/db",
                      "redis://:", "@127.0.0.1:6379/0"):
        assert readable in jsonl_text, f"over-redacted: {readable!r} missing"

    md = trace.render_markdown(t.run_id)
    for secret in secrets:
        assert secret not in md, f"leaked into markdown: {secret!r}"


def test_render_markdown_handles_backticks_and_multiline():
    # objection #4: a response with an embedded backtick and a multi-line
    # shell dump must not break the list item or collapse the newlines.
    tricky = "line one\nline two with a `backtick` inside\nline three"
    with trace.Trace("markdown-agent", "run a shell command") as t:
        t.step("ran command", tool="bash", args={"cmd": "echo hi"}, response=tricky)
        t.result = {"status": "ok", "outcome": "done"}
    md = trace.render_markdown(t.run_id)
    assert "line one" in md and "line two" in md and "line three" in md
    assert "```" in md or "````" in md  # fenced, not a broken inline span


def test_render_index_survives_a_truncated_jsonl_file():
    # objection: an interrupted run (Ctrl-C, OOM, laptop sleep) leaves a
    # truncated final line. render_index() must still cover every OTHER
    # agent's runs rather than raising and producing no INDEX.md at all.
    with trace.Trace("healthy-agent", "finished cleanly") as t:
        t.step("did a thing")
        t.result = {"status": "ok", "outcome": "fine"}

    broken_path = trace.TRACE_DIR / "crashed-agent-999.jsonl"
    broken_path.write_text(
        '{"type": "meta", "run_id": "crashed-agent-999", "agent": "crashed-agent", '
        '"instruction": "x", "capture": "captured", "started_at": "2026-01-01T00:00:00Z"}\n'
        '{"type": "step", "step": 0, "action": "mid-writ'  # truncated, no closing brace
    )

    md = trace.render_index()
    assert "healthy-agent" in md
    assert (trace.TRACE_DIR / "INDEX.md").exists()


def test_render_markdown_includes_response_with_no_tool_set():
    # objection: a step logged without tool= silently dropped its args and
    # response from the rendered markdown that judges read, even though the
    # JSONL kept them. Reasoning-only steps (no tool call) are common.
    with trace.Trace("reasoning-agent", "think it through") as t:
        t.step("model reasoned", response="THE IMPORTANT MODEL OUTPUT")
        t.result = {"status": "ok", "outcome": "done"}
    md = trace.render_markdown(t.run_id)
    assert "THE IMPORTANT MODEL OUTPUT" in md


def test_oversized_field_is_truncated():
    huge = "x" * (trace.MAX_FIELD_CHARS + 500)
    with trace.Trace("big-agent", "dump data") as t:
        t.step("dumped", response={"blob": huge})
        t.result = {"status": "ok", "outcome": "done"}
    jsonl_text = (trace.TRACE_DIR / f"{t.run_id}.jsonl").read_text()
    assert "TRUNCATED" in jsonl_text
    assert huge not in jsonl_text


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\n{len(tests)}/{len(tests)} passed")
