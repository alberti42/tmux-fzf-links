### Release 1.4.16

This is a small bug-fix release relevant for users running tmux 3.4 as shipped with Ubuntu 24.04 (`tmux 3.4-1ubuntu0.1`).

#### Fixes
- **tmux 3.4 compatibility**: Fixed a regression where `display-message -p` on tmux 3.4 (notably the `tmux 3.4-1ubuntu0.1` build shipped with Ubuntu 24.04) escapes the unit-separator byte (`\x1f`) used as an internal field delimiter into the literal 4-character string `\037`. This caused `@fzf-links-fzf-display-options` to be parsed incorrectly, surfacing as errors like `fzf failed with exit code 2: unknown option: --no-preview\037`. Thanks to @wogong for the report and fix (#18).
