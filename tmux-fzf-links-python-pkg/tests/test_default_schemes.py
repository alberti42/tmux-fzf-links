import pytest

from tmux_fzf_links.default_schemes import trim_url, url_scheme


@pytest.mark.parametrize(
    ("raw", "trimmed"),
    [
        ("https://x.dev/a/b", "https://x.dev/a/b"),
        ("https://x.dev/a/b).", "https://x.dev/a/b"),
        ("https://x.dev/a/b.", "https://x.dev/a/b"),
        ("https://x.dev/a/b,", "https://x.dev/a/b"),
        ("https://x.dev/a/b;", "https://x.dev/a/b"),
        ("https://x.dev/a/b:", "https://x.dev/a/b"),
        ("https://x.dev/a/b!", "https://x.dev/a/b"),
        ("https://x.dev/a/b?", "https://x.dev/a/b"),
        ("https://x.dev/a/b'", "https://x.dev/a/b"),
        ('https://x.dev/a/b"', "https://x.dev/a/b"),
        ("https://x.dev/a#readme)", "https://x.dev/a#readme"),
        ("https://en.wikipedia.org/wiki/Foo_(bar)", "https://en.wikipedia.org/wiki/Foo_(bar)"),
        ("https://en.wikipedia.org/wiki/Foo_(bar).", "https://en.wikipedia.org/wiki/Foo_(bar)"),
    ],
)
def test_trim_url(raw: str, trimmed: str) -> None:
    assert trim_url(raw) == trimmed


@pytest.mark.parametrize(
    ("text", "wanted"),
    [
        ("(see https://github.com/alberti42/tmux-fzf-links).", "https://github.com/alberti42/tmux-fzf-links"),
        ("docs at https://github.com/alberti42/tmux-fzf-links.", "https://github.com/alberti42/tmux-fzf-links"),
        ("(https://github.com/alberti42/tmux-fzf-links#readme)", "https://github.com/alberti42/tmux-fzf-links#readme"),
        ("see https://en.wikipedia.org/wiki/Foo_(bar) here", "https://en.wikipedia.org/wiki/Foo_(bar)"),
    ],
)
def test_url_scheme_match_is_trimmed(text: str, wanted: str) -> None:
    match = url_scheme["regex"][0].search(text)
    assert match is not None
    assert trim_url(match.group(0)) == wanted
