"""ponytail: one runnable check, plain asserts, no framework.
Run: python3 test_harness.py
"""
import json
import shutil

import harness.trace as trace

shutil.rmtree(trace.TRACE_DIR, ignore_errors=True)


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
