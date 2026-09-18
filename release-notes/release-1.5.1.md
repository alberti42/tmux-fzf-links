### Release 1.5.1

This is a bug-fix release relevant for users whose tmux server was started from a directory that holds a Python file named after a standard library module.

#### Fixes

- **Plugin exited on start when a stray Python file shadowed a standard library module**: `@fzf-links-python-path` is empty unless you set it, which left `PYTHONPATH` ending in a separator. An empty `PYTHONPATH` entry means the directory the interpreter was launched from, and `run-shell` launches it in the working directory of the tmux server rather than the one of the current pane. A file such as `re.py`, `shlex.py` or `logging.py` sitting in that directory was therefore imported in place of the standard library module, and the plugin exited before it could show anything. The plugin now appends the user path only when there is one, and sets `PYTHONSAFEPATH=1`, which stops Python from adding the launch directory on its own account. Both changes are needed, because `PYTHONSAFEPATH` does not filter `PYTHONPATH`. Python honours the variable from 3.11 and ignores it on 3.10, so the required Python version is unchanged.
