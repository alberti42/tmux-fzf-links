# Change log

## Improvements

- Removed dependency on [fzf-tmux](https://github.com/junegunn/fzf/blob/master/bin/fzf-tmux). The plugin makes use of named pipes directly in Python and do not rely on the relatively slow bash script `fzf-tmux`.
- Improved user-defined scheme for IP addresses
- Updated README with examples

## Bug fixes

- Fixed patte
 recognizing git addresses
