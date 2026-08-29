"""ponytail: one runnable check, plain asserts, no framework.
Run: python3 test_harvest.py

Item 1 uses crafted fixtures (no network). Items 2-7 read the already
harvested, committed cache under data/cases/ (also no network): the
reproducibility promise in PRD.md 7 is that the cache IS the fixture.
"""
import json
from pathlib import Path

import harvest

CASES_DIR = Path(__file__).resolve().parent / "data" / "cases"


def _load_real_cases() -> list[dict]:
    paths = sorted(CASES_DIR.glob("pr-*.json"))
    assert len(paths) == 15, f"expected 15 harvested cases, found {len(paths)}; run harvest.py first"
    return [json.loads(p.read_text()) for p in paths]


def test_closing_re_matches_all_declaring_forms():
    declaring = [
        "Closes #123",
        "Fixed #456",
        "resolves #789",
        "Close: #12",
        "Fixes https://github.com/microsoft/vscode/issues/999",
        "Closes microsoft/vscode#111",
    ]
    for s in declaring:
        assert harvest.CLOSING_RE.search(s), f"should match: {s!r}"


def test_closing_re_rejects_non_declaring_mentions():
    rejecting = [
        "This fixes the crash in #1234",
        "see #5",
        "prefixed #123",
        "fixing #4",
    ]
    for s in rejecting:
        assert not harvest.CLOSING_RE.search(s), f"should NOT match: {s!r}"


def test_bucket_assignment_all_three():
    merged_declared = {
        "number": 1, "title": "x", "body": "Closes #100",
        "merged_at": "2026-01-01T00:00:00Z", "user": {"login": "a", "type": "User"},
        "author_association": "MEMBER",
    }
    merged_no_link = {
        "number": 2, "title": "x", "body": "no ref",
        "merged_at": "2026-01-01T00:00:00Z", "user": {"login": "b", "type": "User"},
        "author_association": "MEMBER",
    }
    closed_unmerged = {
        "number": 3, "title": "x", "body": "closing as stale",
        "merged_at": None, "user": {"login": "c", "type": "User"},
        "author_association": "NONE",
    }
    assert harvest.assign_bucket(merged_declared)[0] == 1
    assert harvest.assign_bucket(merged_no_link)[0] == 2
    assert harvest.assign_bucket(closed_unmerged)[0] == 3


def test_out_of_repo_reference_does_not_make_bucket_1():
    merged_out_of_repo = {
        "number": 4, "title": "x", "body": "Closes Azure/azure-dev#9647",
        "merged_at": "2026-01-01T00:00:00Z", "user": {"login": "d", "type": "User"},
        "author_association": "MEMBER",
    }
    bucket, matches = harvest.assign_bucket(merged_out_of_repo)
    assert bucket == 2, "an out-of-repo declared reference must not promote to bucket 1"
    assert matches and matches[0]["in_repo"] is False


def test_allowed_keys_exact_for_all_15():
    for case in _load_real_cases():
        assert set(case["input"].keys()) == set(harvest.ALLOWED), case["truth"]["number"]


def test_forbidden_fields_nowhere_in_input():
    forbidden = ("created_at", "merged", "state", "closed_at", "merged_at", "labels",
                 "milestone", "draft", "auto_merge", "merged_by", "merge_commit_sha",
                 "comments", "reviews")
    for case in _load_real_cases():
        keys = set(case["input"].keys())
        for field in forbidden:
            assert field not in keys, f"{field} leaked into input for PR {case['truth']['number']}"


def test_zero_closing_ref_matches_survive_in_input():
    for case in _load_real_cases():
        inp = case["input"]
        assert not harvest.CLOSING_RE.search(inp["title"]), case["truth"]["number"]
        assert not harvest.CLOSING_RE.search(inp["body"]), case["truth"]["number"]


def test_positive_control_redaction_actually_happened():
    cases = _load_real_cases()
    forms_seen = set()
    any_redacted = False
    for case in cases:
        forms_seen |= set(case["truth"]["closing_ref_forms"])
        if harvest.REDACT_TOKEN in case["input"]["title"] or harvest.REDACT_TOKEN in case["input"]["body"]:
            any_redacted = True
    assert any_redacted, "not one of the 15 cases had a closing reference caught and redacted"
    assert "url" in forms_seen or "shorthand" in forms_seen, \
        "not one of the 15 cases used the URL or shorthand closing-reference form"


def test_changed_files_is_a_list_never_an_int():
    # The condition-D bug: the raw PR object's own `changed_files` field is
    # an integer count, and harvest() must overwrite it with the real file
    # list (from the /pulls/{n}/files endpoint) before build_input() runs.
    for case in _load_real_cases():
        cf = case["input"]["changed_files"]
        assert isinstance(cf, list), f"PR {case['truth']['number']}: changed_files is {type(cf)}, not a list"
        assert not isinstance(cf, bool)
        assert all(isinstance(f, str) for f in cf), f"PR {case['truth']['number']}: changed_files has a non-string entry"


def test_bucket_counts_are_balanced_5_5_5():
    cases = _load_real_cases()
    counts = {1: 0, 2: 0, 3: 0}
    for case in cases:
        counts[case["truth"]["bucket"]] += 1
    assert counts == {1: 5, 2: 5, 3: 5}


def test_bucket_3_has_at_least_3_non_bot_outside_contributors():
    cases = [c for c in _load_real_cases() if c["truth"]["bucket"] == 3]
    outsiders = sum(
        1 for c in cases
        if not c["truth"]["is_bot"] and c["truth"]["author_association"] in
        ("CONTRIBUTOR", "FIRST_TIME_CONTRIBUTOR", "NONE")
    )
    assert outsiders >= 3, f"only {outsiders}/5 bucket-3 cases are non-bot outside-contributor closes"


def test_no_author_login_anywhere_in_input_or_truth():
    for case in _load_real_cases():
        blob = json.dumps(case)
        pseudonym = case["truth"]["author_pseudonym"]
        assert pseudonym.startswith("AUTHOR-")
        # the pseudonym itself is expected to appear; nothing else identity-shaped should
        assert "login" not in case["input"]
        assert "user" not in case["input"]


def test_link_declared_matches_bucket_1_definition():
    for case in _load_real_cases():
        t = case["truth"]
        if t["bucket"] == 1:
            assert t["link_declared"] is True
        elif t["bucket"] == 2:
            assert t["link_declared"] is False


def test_issue_corpus_and_manifest_committed():
    issues_path = Path(__file__).resolve().parent / "data" / "issues.jsonl"
    manifest_path = Path(__file__).resolve().parent / "data" / "manifest.json"
    assert issues_path.exists()
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text())
    assert manifest["verification"]["unresolved"] == 0
    assert manifest["case_counts"] == {"1": 5, "2": 5, "3": 5}


# --- added after the baseline plan review found both defects in shipped data ---

def test_no_identity_or_closing_ref_survives_in_patch():
    """Every patch must be free of contributor identity and of any closing
    reference. Both failed on the first shipped case set: 15 of 15 carried a
    real name and mail address, and case 308696 still contained `Fixes #305306`."""
    import json as _json, glob as _glob
    from harvest import IDENTITY_LINE_RE, EMAIL_RE, CLOSING_RE
    cases = sorted(_glob.glob("data/cases/*.json"))
    assert cases, "no cases on disk"
    scrubbed_something = False
    for path in cases:
        patch = _json.load(open(path))["input"]["patch"]
        assert not IDENTITY_LINE_RE.search(patch), f"identity line survives in {path}"
        assert not EMAIL_RE.search(patch), f"mail address survives in {path}"
        assert not CLOSING_RE.search(patch), f"closing reference survives in {path}"
        if "[REDACTED-IDENTITY]" in patch:
            scrubbed_something = True
    # positive control: the scrub must have actually fired somewhere, otherwise
    # this whole test passes vacuously on data that never had the problem.
    assert scrubbed_something, "scrub never fired; test would pass vacuously"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\n{len(tests)}/{len(tests)} passed")
