#!/usr/bin/env python3
"""What the author-declared chip is allowed to claim, and nothing more.

The chip says a closing reference APPEARS in the author's own text. It does not
say the author meant it, because a regex cannot know that. So the one thing
that has to hold is that the reader sees the author's words: a negation, an
unticked checkbox or a quote marker must survive into the rendered quote, or
the chip reads as an endorsement of something the author was denying.

Offline. No network, no credential, no model. Part of ./run.sh eval.
"""
import live


class Everything:
    """Stands in for the resolver. These strings are about extraction and
    quoting, so nothing here may depend on an issue really existing."""

    def classify(self, n, repo=None):
        return "open"


def refs(text, repo="microsoft/vscode"):
    return live.declared_refs({"title": text, "body": ""}, repo, Everything())


# (text, what the reader must be able to see in the quote)
QUOTES = [
    ("This does not fix #123", "This does not fix #123"),
    ("It will not close #777 yet", "It will not close #777"),
    ("Do NOT resolve #888", "Do NOT resolve #888"),
    ("- [ ] Fixes #999", "- [ ] Fixes #999"),
    ("> Fixes #4242", "> Fixes #4242"),
    ("I spent a day on this and concluded the change does not fix #123",
     "does not fix #123"),
]


def main():
    checks = 0
    for text, must_contain in QUOTES:
        got = refs(text)
        assert len(got) == 1, (text, got)
        assert must_contain in got[0]["quote"], (text, got[0]["quote"])
        checks += 1

    # the standard pull-request template placeholder is not a declaration
    assert refs("Fixes #<issue number>") == []
    # nor is an example inside a fenced code block
    assert refs("how to use it\n```\nFixes #555\n```\ndone") == []
    checks += 2

    # the number is never truncated off the end of a chip that says "confirmed"
    url = refs("Fixes https://github.com/other/proj/issues/77")
    assert url[0]["quote"].endswith("/issues/77"), url
    assert (url[0]["owner"], url[0]["repo"]) == ("other", "proj"), url
    assert url[0]["same_repo"] is False
    checks += 1

    # a bare #N belongs to the repository we were pointed at, never to vscode
    bare = refs("Fixes #7", repo="acme/widgets")
    assert (bare[0]["owner"], bare[0]["repo"]) == ("acme", "widgets"), bare
    assert bare[0]["same_repo"] is True
    checks += 1

    # title and body repeat the same reference; the card says it once
    both = live.declared_refs({"title": "Fix #231076: restore it",
                               "body": "Fixes #231076 on Windows"},
                              "microsoft/vscode", Everything())
    assert len(both) == 1 and both[0]["quote"] == "Fix #231076", both
    checks += 1

    print(f"declared references: {checks}/{checks} checks passed")


if __name__ == "__main__":
    main()
