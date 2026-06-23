# ===============================================================================
#   Author: (c) 2024 Andrea Alberti
# ===============================================================================

"""OSC 8 hyperlink support.

Terminals can wrap on-screen text in an OSC 8 escape sequence whose payload is
the canonical target URL:

    ESC ] 8 ; params ; URI ST  visible-text  ESC ] 8 ; ; ST

`tmux capture-pane -p` strips these sequences; `capture-pane -p -e` keeps them.
This module parses the escaped capture so the plugin can:

- surface each hyperlink as a first-class match (see the built-in OSC 8 scheme
  in ``default_schemes``); and
- expose a ``visible-text -> URI`` map that any handler can consult via
  ``target_for`` to resolve an ambiguous token (e.g. ``#497``) to the URL it was
  actually linked to.

It also reconstructs the plain capture from the escaped one via ``strip_escapes``
so the remaining (non-escaped) schemes match exactly what they did before.
"""

from __future__ import annotations

import bisect
import re
from collections.abc import Callable

# ST (string terminator) is ESC \ or BEL. The URI runs to the terminator. The
# visible text may carry its own SGR color codes, stripped out below.
_ST = r"(?:\x1b\\|\x07)"
_HYPERLINK = re.compile(
    rf"\x1b\]8;[^;]*;(?P<uri>[^\x1b\x07]*){_ST}(?P<text>.*?)\x1b\]8;;{_ST}",
    re.DOTALL,
)
# Any OSC 8 marker (open or close), used to scrub orphans left when a hyperlink
# is split across the capture boundary.
_OSC8_ANY = re.compile(rf"\x1b\]8;[^\x1b\x07]*{_ST}")
# SGR and other CSI sequences carried inside the visible text.
_ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def hyperlink_regex() -> re.Pattern[str]:
    """The compiled OSC 8 pattern, exposed for the built-in scheme."""
    return _HYPERLINK


def clean_text(text: str) -> str:
    """Strip SGR codes from a hyperlink's visible text."""
    return _ANSI.sub("", text).strip()


def strip_escapes(data: str) -> str:
    """Reconstruct the plain capture from an escaped one.

    Keeps each hyperlink's visible text and drops the OSC 8 wrappers and SGR
    codes, yielding what ``capture-pane -p`` (without ``-e``) would have
    produced for the same region.
    """
    data = _HYPERLINK.sub(lambda m: m.group("text"), data)
    data = _OSC8_ANY.sub("", data)
    data = _ANSI.sub("", data)
    return data


def offset_translator(data: str) -> Callable[[int], int]:
    """Map an index into the escaped capture to the matching index into
    ``strip_escapes(data)``.

    ``strip_escapes`` drops exactly the OSC 8 markers and SGR sequences, so a
    plain-text offset is the escaped offset minus the escape bytes preceding it.
    The translator is built in one pass and answers each query in O(log n), so a
    caller mapping many match offsets never re-strips the capture prefix.
    """
    spans = sorted(
        [m.span() for m in _OSC8_ANY.finditer(data)]
        + [m.span() for m in _ANSI.finditer(data)]
    )
    ends: list[int] = []
    removed_through: list[int] = []
    removed = 0
    for start, end in spans:
        removed += end - start
        ends.append(end)
        removed_through.append(removed)

    def translate(offset: int) -> int:
        # Only sequences that fully end at or before the offset are gone from
        # the plain prefix. One straddling the offset is an incomplete sequence
        # that strip_escapes leaves in place.
        k = bisect.bisect_right(ends, offset)
        return offset - (removed_through[k - 1] if k else 0)

    return translate


def parse_links(data: str) -> dict[str, str]:
    """Map each hyperlink's visible text to its target URI.

    Text that appears with conflicting URIs is dropped so a lookup never
    resolves to the wrong target.
    """
    found: dict[str, str | None] = {}
    for m in _HYPERLINK.finditer(data):
        text = clean_text(m.group("text"))
        uri = m.group("uri").strip()
        if not text or not uri:
            continue
        if text in found and found[text] != uri:
            found[text] = None
        else:
            found.setdefault(text, uri)
    return {text: uri for text, uri in found.items() if uri}


def url_kind(url: str) -> str:
    """Classify a forge URL as 'pr', 'issue', 'commit', or 'other'."""
    if "/pull/" in url or "/merge_requests/" in url:
        return "pr"
    if "/issues/" in url:
        return "issue"
    if "/commit/" in url:
        return "commit"
    return "other"


# Module-level map populated by the plugin before matching, so that handlers in
# user schemes can resolve a matched token to the URL it was hyperlinked to.
_links: dict[str, str] = {}


def set_links(links: dict[str, str]) -> None:
    """Install the ``visible-text -> URI`` map for the current capture."""
    global _links
    _links = links


def target_for(text: str) -> str | None:
    """Resolve a matched token to the URL it was hyperlinked to, if any."""
    return _links.get(text)


__all__ = [
    "hyperlink_regex",
    "clean_text",
    "strip_escapes",
    "offset_translator",
    "parse_links",
    "url_kind",
    "set_links",
    "target_for",
]
