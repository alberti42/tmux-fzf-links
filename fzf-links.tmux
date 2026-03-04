#!/usr/bin/env -S /opt/homebrew/bin/bash --noprofile --norc

# Andrea Alberti, 2024

# Start profiling the entire script load time
_prof_start=$EPOCHREALTIME

# Resolve the directory containing this script
SCRIPT_DIR=${BASH_SOURCE[0]%/*}

# $1: option
# $2: default value
tmux_get() {
  local tmux_param_name=$1
  local default_param=$2
  local value

  value=$(tmux show -gqv "$tmux_param_name")
  if [[ -n "$value" ]]; then
      printf '%s\n' "$value"
  else
      printf '%s\n' "$default_param"
  fi
}

# Pure Bash expansion for ~ (Zero forks, zero subshells)
# Set the result into $REPLY
expand_vars() {
  if [[ "$1" == "~/"* ]]; then
      REPLY="${HOME}${1:1}"
  elif [[ "$1" == "~" ]]; then
      REPLY="${HOME}"
  else
      REPLY="$1"
  fi
}

# Set browser open command default based on OS
case "$OSTYPE" in
  darwin*) browser_open_default="open '%url'" ;;
  *)       browser_open_default="xdg-open '%url'" ;;
esac

# Fetch Tmux options with defaults
key=$(tmux_get '@fzf-links-key' 'C-h')
history_lines=$(tmux_get '@fzf-links-history-lines' '0')
editor_open_cmd=$(tmux_get '@fzf-links-editor-open-cmd' "tmux new-window -n 'vim' vim +%line '%file'")
browser_open_cmd=$(tmux_get '@fzf-links-browser-open-cmd' "$browser_open_default")
fzf_path=$(tmux_get '@fzf-links-fzf-path' 'fzf')
fzf_display_options=$(tmux_get '@fzf-links-fzf-display-options' '-w 100% --maxnum-displayed 20 --multi --track --no-preview')
path_extension=$(tmux_get '@fzf-links-path-extension' '')
loglevel_tmux=$(tmux_get '@fzf-links-loglevel-tmux' 'WARNING')
loglevel_file=$(tmux_get '@fzf-links-loglevel-file' 'DEBUG')
log_filename=$(tmux_get '@fzf-links-log-filename' '')
python=$(tmux_get '@fzf-links-python' 'python3')
python_path=$(tmux_get '@fzf-links-python-path' '')
use_colors=$(tmux_get '@fzf-links-use-colors' 'on')
ls_colors_filename=$(tmux_get '@fzf-links-ls-colors-filename' '')
user_schemes_path=$(tmux_get '@fzf-links-user-schemes-path' '')
hide_fzf_header=$(tmux_get '@fzf-links-hide-fzf-header' 'DEPRECATED')
hide_bottom_bar=$(tmux_get '@fzf-links-hide-bottom-bar' 'off') # deprecated option

# End profiling the entire script load time
_prof_end=$EPOCHREALTIME

# Log the total load duration in milliseconds to ~/tmux-fzf-links.log
# Note: This includes the time spent calling `tmux show` for options.
python3 -c "print(f'$(date): Full plugin load took {int(($_prof_end - $_prof_start) * 1000)}ms')" >> ~/tmux-fzf-links.log


# Expand variables to resolve ~ and environment variables (e.g. $HOME)
expand_vars "$path_extension"; path_extension="$REPLY"
expand_vars "$log_filename"; log_filename="$REPLY"
expand_vars "$python"; python="$REPLY"
expand_vars "$python_path"; python_path="$REPLY"
expand_vars "$ls_colors_filename"; ls_colors_filename="$REPLY"
expand_vars "$user_schemes_path"; user_schemes_path="$REPLY"
expand_vars "$fzf_path"; fzf_path="$REPLY"

# Resolve python to an absolute path if possible; fall back to the given string
if python_resolved=$(command -v -- "$python" 2>/dev/null); then
  python="$python_resolved"
fi

# Prebuild a fully quoted command line (safe for /bin/sh in run-shell)
quote() { printf "%q" "$1"; }

PYENV="PYTHONPATH=$SCRIPT_DIR/tmux-fzf-links-python-pkg:$python_path"

# Arguments to the module, in order
args=(
  -m tmux_fzf_links
  "$history_lines" "$editor_open_cmd" "$browser_open_cmd"
  "$fzf_path" "$fzf_display_options" "$path_extension"
  "$loglevel_tmux" "$loglevel_file" "$log_filename"
  "$user_schemes_path" "$use_colors" "$ls_colors_filename"
  "$hide_bottom_bar" "$hide_fzf_header"
)

# Build the one-liner to hand to tmux (no arrays inside tmux; plain sh is fine)
cmd=$(printf "%q " env "$PYENV" "$python" "${args[@]}")
cmd=${cmd% }   # strip trailing space in $cmd

# Bind the key in Tmux to run the Python script
tmux bind-key -N "Open links with fuzzy finder (tmux-fzf-links plugin)" "$key" run-shell "
# If python is not an executable path, just report and exit.
if [ ! -x $(quote "$python") ]; then
  tmux display-message -d 0 'fzf-links: no executable python found at: '$(quote "$python")
  exit 0
fi

# Run the command via /bin/sh-compatible syntax; capture status
$cmd 2>&1
status=\$?

if [ \$status -ne 0 ]; then
  tmux display-message -d 0 \"fzf-links: Python script unexpectedly exited with status \$status\"
  printf '%s\n\n' 'If you want to reproduce (and possibly debug) the error, run in your shell the command below:'
  printf '%s\n' \"$cmd\"
fi
"