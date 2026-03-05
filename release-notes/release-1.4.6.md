# Change log

## Bug fixes

- Removed detection of binary files; this was preventing the user from revealing binary files in the system's file explorer and opening them with the system's default opener.

## Small improvements

- Deprecated tmux variable `@fzf-links-hide-fzf-header`; replace it with `fzf-links-hide-bottom-bar`. In the long term, the tmux variable `fzf-links-hide-fzf-header` will be discontinued, and only `fzf-links-hide-bottom-bar` will be supported.
