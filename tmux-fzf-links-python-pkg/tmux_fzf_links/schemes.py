# ===============================================================================
#   Author: (c) 2024 Andrea Alberti
# ===============================================================================

import errno
from os.path import expanduser
from pathlib import Path


def heuristic_find_file(file_path_str: str) -> Path | None:

    try:
        # Expand tilde (~) to the user's home directory
        file_path = Path(expanduser(file_path_str))
        # Check if the file exists either as is or relative to the current directory
        if file_path.exists():
            return file_path.resolve()  # Return the absolute resolved path
        else:
            # Drop the match if it corresponds to no file
            return None
    except OSError as e:
        # Filename too long
        if e.errno == errno.ENAMETOOLONG:
            return None
        else:
            raise e


_URL_TRAILING_PUNCTUATION = ".,;:!?'\""


def trim_url(url: str) -> str:
    """Strip the punctuation that prose puts after a URL.

    A trailing period, comma or quote is never part of the URL. A closing
    parenthesis is dropped only when the URL holds no opening partner for it,
    so `https://en.wikipedia.org/wiki/Foo_(bar)` survives while the `)` that
    closes `(see https://example.com/a)` does not.
    """
    opens = url.count("(")
    closes = url.count(")")
    while url:
        last = url[-1]
        if last in _URL_TRAILING_PUNCTUATION:
            url = url[:-1]
        elif last == ")" and opens < closes:
            url = url[:-1]
            closes -= 1
        else:
            break
    return url


__all__ = ["heuristic_find_file", "trim_url"]
