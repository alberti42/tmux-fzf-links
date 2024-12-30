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

key=$(tmux_get '@fzf-url-bind' 'o')
history_limit=$(tmux_get '@fzf-url-history-limit' 'screen')
extra_filter=$(tmux_get '@fzf-url-extra-filter' '')
custom_open=$(tmux_get '@fzf-url-open' '')
fzf_options=$(tmux_get '@fzf-url-fzf-options')
extra_path=$(tmux_get '@fzf-url-extra-path' '')

# Ensure parameters are safely passed, even if they are empty strings
tmux bind-key "$key" run-shell -b "$SCRIPT_DIR/fzf-url.zsh '$extra_filter' '$history_limit' '$custom_open' '$fzf_options' '$extra_path'"
