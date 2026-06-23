import pytest

from tmux_fzf_links.hyperlinks import (
    hyperlink_regex,
    offset_translator,
    parse_links,
    set_links,
    strip_escapes,
    target_for,
    url_kind,
)

ESC = "\x1b"
ST = f"{ESC}\\"


def link(uri: str, text: str, params: str = "") -> str:
    return f"{ESC}]8;{params};{uri}{ST}{text}{ESC}]8;;{ST}"


def test_parse_extracts_text_to_uri() -> None:
    pr = "https://github.com/bendrucker/dotfiles/pull/497"
    data = f"shipped {link(pr, 'bendrucker/dotfiles#497', params='id=7jn05')} today"
    assert parse_links(data) == {"bendrucker/dotfiles#497": pr}


def test_parse_strips_sgr_codes_inside_text() -> None:
    pr = "https://github.com/o/r/pull/497"
    # Tools wrap the visible text in color codes and leave a trailing reset
    # before the closing OSC 8 sequence.
    data = f"{ESC}[94m{link(pr, f'#497{ESC}[0m{ESC}[38;5;246m')}"
    assert parse_links(data) == {"#497": pr}


def test_parse_drops_ambiguous_text() -> None:
    a = link("https://x/issues/1", "#1")
    b = link("https://x/pull/1", "#1")
    assert parse_links(a + b) == {}


def test_parse_accepts_bel_terminator() -> None:
    bel = "\x07"
    uri = "https://example.com/issues/9"
    data = f"{ESC}]8;;{uri}{bel}#9{ESC}]8;;{bel}"
    assert parse_links(data) == {"#9": uri}


def test_parse_ignores_plain_text() -> None:
    assert parse_links("no links here #123") == {}


def test_strip_escapes_keeps_visible_text() -> None:
    pr = "https://github.com/o/r/pull/497"
    data = f"{ESC}[94mshipped {link(pr, '#497')}{ESC}[0m today"
    assert strip_escapes(data) == "shipped #497 today"


def test_strip_escapes_scrubs_orphan_osc8_marker() -> None:
    # A hyperlink split across the capture boundary leaves a lone opener.
    data = f"trailing {ESC}]8;;https://x/issues/1{ST}#1"
    assert strip_escapes(data) == "trailing #1"


def test_strip_escapes_keeps_bel_terminated_text_with_inner_sgr() -> None:
    bel = "\x07"
    uri = "https://github.com/o/r/pull/497"
    # BEL terminator instead of ST, with SGR codes wrapping the visible text.
    data = f"shipped {ESC}]8;;{uri}{bel}{ESC}[94m#497{ESC}[0m{ESC}]8;;{bel} today"
    assert strip_escapes(data) == "shipped #497 today"


@pytest.mark.parametrize(
    ("url", "kind"),
    [
        ("https://github.com/o/r/pull/497", "pr"),
        ("https://gitlab.com/g/p/-/merge_requests/7", "pr"),
        ("https://github.com/o/r/issues/12", "issue"),
        ("https://github.com/o/r/commit/c91b594", "commit"),
        ("https://example.com/whatever", "other"),
    ],
)
def test_url_kind(url: str, kind: str) -> None:
    assert url_kind(url) == kind


def test_target_for_resolves_installed_map() -> None:
    set_links({"#497": "https://github.com/o/r/pull/497"})
    try:
        assert target_for("#497") == "https://github.com/o/r/pull/497"
        assert target_for("#999") is None
    finally:
        set_links({})
    assert target_for("#497") is None


def test_offset_translator_matches_strip_escapes_at_every_index() -> None:
    pr = "https://github.com/o/r/pull/497"
    data = f"{ESC}[94mshipped {link(pr, '#497')}{ESC}[0m and {link(pr, 'again')} end"
    translate = offset_translator(data)
    # The plain offset of any escaped index equals the length of the stripped
    # prefix up to that index. That is the property the picker sort relies on.
    for i in range(len(data) + 1):
        assert translate(i) == len(strip_escapes(data[:i]))


def test_offset_translator_maps_hyperlink_starts_to_on_screen_columns() -> None:
    pr = "https://github.com/o/r/pull/497"
    data = f"see {link(pr, '#497')} now"
    translate = offset_translator(data)
    match = hyperlink_regex().search(data)
    assert match is not None
    # "#497" begins at column 4 on screen ("see ").
    assert translate(match.start()) == 4
