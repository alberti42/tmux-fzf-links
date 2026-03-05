# Change log

## Bug fixes

- Improved stability of the `tmux` script `fzf-links.tmux`, which acts as the launcher of the true Python plugin; it previously failed under Linux because it was not handling correctly `run-shell` command. It was assuming a `bash` process, whereas `tmux` spawns a `sh` process.
