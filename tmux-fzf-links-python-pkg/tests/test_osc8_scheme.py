import pytest

from tmux_fzf_links.colors import colors
from tmux_fzf_links.default_schemes import (
    default_schemes,
    osc8_post_handler,
    osc8_pre_handler,
    osc8_scheme,
)
from tmux_fzf_links.hyperlinks import hyperlink_regex

ESC = "\x1b"
ST = f"{ESC}\\"


def match(uri: str, text: str):
    data = f"{ESC}]8;;{uri}{ST}{text}{ESC}]8;;{ST}"
    m = hyperlink_regex().search(data)
    assert m is not None
    return m


@pytest.fixture(autouse=True)
def _no_colors() -> None:
    colors.enable_colors(False)


@pytest.mark.parametrize(
    ("uri", "tag"),
    [
        ("https://github.com/o/r/pull/497", "PR"),
        ("https://gitlab.com/g/p/-/merge_requests/7", "PR"),
        ("https://github.com/o/r/issues/12", "issue"),
        ("https://github.com/o/r/commit/c91b594", "commit"),
        ("https://example.com/docs", "link"),
    ],
)
def test_pre_handler_labels_by_url_kind(uri: str, tag: str) -> None:
    result = osc8_pre_handler(match(uri, "token"))
    assert result is not None
    assert result["tag"] == tag
    assert result["tag"] in osc8_scheme["tags"]


def test_pre_handler_shows_text_and_target() -> None:
    result = osc8_pre_handler(match("https://example.com/guide", "docs"))
    assert result is not None
    assert result["display_text"] == "docs → https://example.com/guide"


def test_pre_handler_drops_empty_hyperlink() -> None:
    assert osc8_pre_handler(match("https://x/issues/1", "   ")) is None
    assert osc8_pre_handler(match("", "text")) is None


def test_post_handler_returns_target_url() -> None:
    assert osc8_post_handler(match("https://x/pull/9", "#9")) == {
        "url": "https://x/pull/9"
    }


def test_osc8_scheme_matches_escaped_capture_with_hyperlink_regex() -> None:
    # The scheme must opt into the escaped capture and drive matching off the
    # shared OSC 8 pattern. Otherwise it would scan reconstructed plain text and
    # never see a hyperlink.
    assert osc8_scheme.get("escaped") is True
    assert osc8_scheme["regex"] == [hyperlink_regex()]


def test_osc8_tags_are_owned_solely_by_osc8_scheme() -> None:
    # The post-handler is dispatched by the tag parsed out of the fzf line, so a
    # tag shared by two schemes would route to the wrong handler.
    for scheme in default_schemes:
        if scheme is osc8_scheme:
            continue
        assert not set(scheme["tags"]) & set(osc8_scheme["tags"])


def test_relabeled_match_routes_to_osc8_post_handler() -> None:
    # Build tag_to_index exactly as __main__ does, then confirm a dynamically
    # relabeled match (a PR labeled "PR") dispatches back to osc8_scheme.
    tag_to_index = {
        tag: index
        for index, scheme in enumerate(default_schemes)
        for tag in scheme.get("tags", ())
    }
    m = match("https://github.com/o/r/pull/497", "#497")
    pre = osc8_pre_handler(m)
    assert pre is not None and pre["tag"] == "PR"

    scheme = default_schemes[tag_to_index[pre["tag"]]]
    assert scheme is osc8_scheme
    assert scheme["post_handler"] is not None
    assert scheme["post_handler"](m) == {"url": "https://github.com/o/r/pull/497"}
