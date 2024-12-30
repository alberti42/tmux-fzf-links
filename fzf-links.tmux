#!/usr/bin/env zsh
#===============================================================================
#   Author: (c) 2018 Wenxuan
#   Author: (c) 2024 Andrea Alberti
#===============================================================================

# To ensure safe execution on all zsh systems
emulate -LR zsh

0="${${ZERO:-${0:#$ZSH_ARGZERO}}:-${(%):-%N}}"
0="${${(M)0:#/*}:-$PWD/$0}"

SCRIPT_DIR="${0:h}"

# $1: option
# $2: default value
tmux_get() {
    local value
    value=$(tmux show -gqv "$1")
    [[ -n "$value" ]] && echo "$value" || echo "$2"
}

key=$(tmux_get '@fzf-links-key' 'o')
history_limit=$(tmux_get '@fzf-links-history-limit' 'screen')
editor_open_cmd=$(tmux_get '@fzf-links-editor-open-cmd' '')
browser_open_cmd=$(tmux_get '@fzf-links-browser-open-cmd' '')
fzf_display_options=$(tmux_get '@fzf-links-fzf-display-options' '-w 100% -h 50% --multi -0 --no-preview')
path_extension=$(tmux_get '@fzf-links-path-extension' '')

# Ensure parameters are safely passed, even if they are empty strings
tmux bind-key "$key" run-shell -b "python3 $SCRIPT_DIR/fzf-links.py '$history_limit' '$editor_open_cmd' '$browser_open_cmd' $fzf_display_options' '$path_extension'"
