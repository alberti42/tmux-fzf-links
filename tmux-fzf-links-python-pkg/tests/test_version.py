"""Check that every place the repository declares a version agrees.

The version lives in two places that a release has to touch together:
`setup.py` and the newest file under `release-notes/`. Bumping one and
forgetting the other ships a package whose metadata names the wrong release,
which nothing else would catch.
"""

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SETUP_PY = REPO_ROOT / "tmux-fzf-links-python-pkg" / "setup.py"
RELEASE_NOTES_DIR = REPO_ROOT / "release-notes"

_RELEASE_NOTE_NAME = re.compile(r"^release-(?P<version>\d+(?:\.\d+)*)\.md$")


def setup_py_version() -> str:
    """The version passed to setup(), read without executing setup.py."""
    tree = ast.parse(SETUP_PY.read_text(), filename=str(SETUP_PY))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (isinstance(node.func, ast.Name) and node.func.id == "setup"):
            continue
        for keyword in node.keywords:
            if keyword.arg == "version" and isinstance(keyword.value, ast.Constant):
                assert isinstance(keyword.value.value, str)
                return keyword.value.value
    raise AssertionError(f"no setup(version=...) found in {SETUP_PY}")


def newest_release_note() -> tuple[str, Path]:
    """The highest-numbered release note, as (version, path)."""
    notes: list[tuple[tuple[int, ...], str, Path]] = []
    for path in RELEASE_NOTES_DIR.iterdir():
        match = _RELEASE_NOTE_NAME.match(path.name)
        if match:
            version = match.group("version")
            notes.append((tuple(int(p) for p in version.split(".")), version, path))
    assert notes, f"no release notes found in {RELEASE_NOTES_DIR}"
    _, version, path = max(notes)
    return version, path


def test_setup_py_matches_newest_release_note() -> None:
    version, path = newest_release_note()
    assert setup_py_version() == version, (
        f"setup.py declares {setup_py_version()}, "
        + f"whereas the newest release note is {path.name}"
    )


def test_release_note_heading_matches_its_filename() -> None:
    version, path = newest_release_note()
    first_line = path.read_text().splitlines()[0]
    assert first_line == f"### Release {version}", (
        f"{path.name} opens with {first_line!r}, "
        + f"whereas its filename says version {version}"
    )
