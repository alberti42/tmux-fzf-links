# Change log

## Improvements

- Fixed a bug where the terminal was freezing when opening for the first time an external program like the browser; the reason was that the new process (the browser) was created as a child of the tmux plugin. Now, the new process is started and made independent of the `tmux-fzf-links` plugin (see issue https://github.com/alberti42/tmux-fzf-links/issues/8).
- Added documentation on how to open `vim` or `emacs` in the same tmux window instead of opening a dedicated new tmux window (see issue https://github.com/alberti42/tmux-fzf-links/issues/7)
