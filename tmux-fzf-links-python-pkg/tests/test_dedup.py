import re

from tmux_fzf_links.__main__ import drop_hyperlinked_duplicates
from tmux_fzf_links.hyperlinks import hyperlink_regex
from tmux_fzf_links.opener import PreHandledMatch

ESC = "\x1b"
ST = f"{ESC}\\"

Item = tuple[PreHandledMatch, str, int, re.Match[str]]


def osc8_item(uri: str, text: str) -> Item:
    m = hyperlink_regex().search(f"{ESC}]8;;{uri}{ST}{text}{ESC}]8;;{ST}")
    assert m is not None
    pre: PreHandledMatch = {"display_text": text, "tag": "link"}
    return (pre, m.group(0), 0, m)


def plain_item(text: str) -> Item:
    m = re.compile(r".+").search(text)
    assert m is not None
    pre: PreHandledMatch = {"display_text": text, "tag": "url"}
    return (pre, m.group(0), 0, m)


def test_drops_plain_url_that_was_hyperlinked_to_itself() -> None:
    url = "https://example.com/guide"
    items = [osc8_item(url, url), plain_item(url)]
    out = drop_hyperlinked_duplicates(items)
    assert len(out) == 1
    assert out[0][3].re is hyperlink_regex()


def test_keeps_unrelated_match_sharing_a_hyperlink_label() -> None:
    # A filename that merely shares a hyperlink's visible text resolves to a
    # different target, so it must not be dropped.
    items = [osc8_item("https://docs.example.com", "foo.txt"), plain_item("foo.txt")]
    out = drop_hyperlinked_duplicates(items)
    assert len(out) == 2


def test_keeps_plain_text_when_hyperlink_target_differs() -> None:
    # A shortened label hyperlinked to a different URL: the plain occurrence of
    # the label opens a distinct destination and is worth keeping.
    items = [
        osc8_item("https://long.example.com/full", "https://sho.rt/x"),
        plain_item("https://sho.rt/x"),
    ]
    out = drop_hyperlinked_duplicates(items)
    assert len(out) == 2


def test_drops_plain_match_when_multiple_hyperlinks_share_target() -> None:
    # Two hyperlinks point at the same URL under different labels, plus a bare
    # occurrence of that URL. Both hyperlinks survive. Only the plain match drops.
    url = "https://example.com/guide"
    items = [osc8_item(url, "guide"), osc8_item(url, "docs"), plain_item(url)]
    out = drop_hyperlinked_duplicates(items)
    assert len(out) == 2
    assert all(item[3].re is hyperlink_regex() for item in out)


def test_no_hyperlinks_leaves_items_untouched() -> None:
    items = [plain_item("foo"), plain_item("bar")]
    assert drop_hyperlinked_duplicates(items) == items
