#!/usr/bin/env bash
#===============================================================================
#   Author: (c) 2018 Wenxuan
#   Author: (c) 2024 Andrea Alberti
#===============================================================================

# Resolve the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# $1: option
# $2: default value
tmux_get() {
  local tmux_param_name=$1
  local default_param=$2
  local value
  
  value=$(tmux show -gqv "$tmux_param_name")
  if [[ -n "$value" ]]; then
      echo "$value"
  else
      echo "$default_param"
  fi
}

# Fetch Tmux options with defaults
key=$(tmux_get '@fzf-links-key' 'o')
history_limit=$(tmux_get '@fzf-links-history-limit' 'screen')
editor_open_cmd=$(tmux_get '@fzf-links-editor-open-cmd' '')
browser_open_cmd=$(tmux_get '@fzf-links-browser-open-cmd' '')
fzf_display_options=$(tmux_get '@fzf-links-fzf-display-options' '-w 100% -h 50% --multi -0 --no-preview')
path_extension=$(tmux_get '@fzf-links-path-extension' '')
verbose=$(tmux_get '@fzf-links-verbose' 'off')

# Bind the key in Tmux to run the Python script
tmux bind-key "$key" run-shell -b "python3 $SCRIPT_DIR/fzf-links.py '$history_limit' '$editor_open_cmd' '$browser_open_cmd' '$fzf_display_options' '$path_extension' '$verbose'"
