### Release 1.4.17

This release adds support for OSC 8 hyperlinks, so that a token such as `#497` opens the URL the tool that printed it linked to. It also fixes four bugs, one of which made every invocation fail for users who set `--tmux` (or its newer name `--popup`) in their `fzf` configuration.

#### Requirements

- **fzf 0.53 or newer** is now required. This is the release that introduced the `--no-tmux` option on which the fix below relies.
- **tmux 3.4 or newer** is required for the OSC 8 hyperlinks below, because that is the release in which tmux started recording them. On an older tmux the hyperlink scheme finds nothing and the rest of the plugin works as before.

#### New Features

- **OSC 8 hyperlinks**: Tools such as `gh`, `delta` and CI output wrap on-screen text in an OSC 8 escape sequence that carries the target URL, so that `#497` on screen stands for `https://github.com/owner/repo/pull/497`. The plugin now captures the pane with `tmux capture-pane -e`, which keeps those sequences, and lists every hyperlink as its own entry, tagged `PR`, `issue`, `commit` or `link` according to its target. Selecting `#497` opens that URL, so the plugin no longer has to guess what an ambiguous token means. A user scheme can read the same information by calling `target_for`, which maps a visible token to the URL it was linked to; a scheme that sets `"escaped": True` matches the escaped capture instead of the reconstructed plain text. See *Resolving OSC 8 Hyperlinks* in the README. Thanks to @bendrucker for writing the feature (#22).

#### Fixes

- **Python older than 3.10 reported as a syntax error**: When `@fzf-links-python` is unset, the plugin runs whichever `python3` it finds on `PATH`. On macOS without current Command Line Tools that can be a working 3.9 interpreter, and the package needs 3.10 or newer, so the first key press failed with a `SyntaxError` raised deep inside `__main__.py`. The plugin now reads the interpreter's version when it loads and reports `requires python >= 3.10, found <version> at <path> (set @fzf-links-python)`. A missing interpreter still produces its own, separate message. Thanks to @bendrucker for the report and fix (#20).

- **URLs opened with trailing punctuation**: The regex of the `url` scheme pulls a trailing period, comma or closing parenthesis into the match, so a URL written in prose, as in `(see https://example.com/a).`, was opened as `https://example.com/a).` and produced a 404. The plugin now strips trailing punctuation from the match before opening it. It removes a closing parenthesis only when the match holds no opening partner for it, so a URL such as `https://en.wikipedia.org/wiki/Foo_(bar)` stays intact. Thanks to @bendrucker for the report and fix (#21).

- **`unexpected runtime error: list index out of range`**: Fixed a failure that occurred on every invocation of the plugin when `--tmux`, or its newer name `--popup`, was set in `FZF_DEFAULT_OPTS`, in the file pointed to by `FZF_DEFAULT_OPTS_FILE`, or in `@fzf-links-fzf-display-options`. These options instruct `fzf` to display itself in a tmux popup, but the plugin already runs `fzf` inside a popup that it creates and manages itself. As tmux silently ignores a popup requested from within a popup, `fzf` exited with status 0 without printing anything, not even the action bound to the key that was pressed, and reading that empty output raised an `IndexError`. The plugin now appends `--no-tmux` after the user options, where it cannot be overridden. Thanks to @stephansama for reporting the problem and to @wushenrong for confirming it (#16).

- **Duplicate entry for a hyperlinked URL in parentheses**: A URL that the terminal had wrapped in an OSC 8 hyperlink appeared twice in the picker when the text around it ended in a closing parenthesis, as in `(https://example.com/pull/167)`. The hyperlink carries the bare URL as its target, whereas the plain-text match kept the trailing `)`. The two strings therefore differed, and the step that drops a plain match already covered by a hyperlink left both entries in place. The plain match is now stripped of wrapping punctuation before that comparison, using the same trimming the plugin already applies before opening the URL. Thanks to @deferred for the report and fix (#23).

#### Improvements

- **Colors that follow the terminal theme**: The picker set the index, the tags and the separator to absolute RGB values, which washed out on a light background such as Catppuccin Latte. It now emits ANSI 16-color codes, so the terminal's theme picks each shade: the index is bold blue, every tag is cyan, the separator is dim, and the match text carries the color of its type — blue for git, red for code errors, magenta for URLs, and `$LS_COLORS` for files and directories. Green and yellow are no longer used, as both are low-contrast on light themes. The color scheme is documented in the README.

- **Better diagnostics**: `fzf` returning no output at all is now reported as a descriptive error naming the options to check, instead of surfacing as an unexpected runtime error. Unexpected errors are moreover logged with a traceback, so that the origin of a failure can be located in the log file configured with `@fzf-links-log-filename`.
