#!/usr/bin/env -S /opt/homebrew/bin/bash --noprofile --norc

# Andrea Alberti, 2024

# Start profiling the entire script load time
_prof_start=$EPOCHREALTIME

# Resolve the directory containing this script
SCRIPT_DIR=${BASH_SOURCE[0]%/*}

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

# Fetch Tmux options with defaults in a SINGLE call for performance (approx 5ms vs 80ms)
# We use a unique separator to handle potentially empty options correctly.
_bulk_options=$(tmux display-message -p \
"#{@fzf-links-key}
#{@fzf-links-history-lines}
#{@fzf-links-editor-open-cmd}
#{@fzf-links-browser-open-cmd}
#{@fzf-links-fzf-path}
#{@fzf-links-fzf-display-options}
#{@fzf-links-path-extension}
#{@fzf-links-loglevel-tmux}
#{@fzf-links-loglevel-file}
#{@fzf-links-log-filename}
#{@fzf-links-python}
#{@fzf-links-python-path}
#{@fzf-links-use-colors}
#{@fzf-links-ls-colors-filename}
#{@fzf-links-user-schemes-path}
#{@fzf-links-hide-fzf-header}
#{@fzf-links-hide-bottom-bar}
END_MARKER")
# We add END_MARKER to prevent Bash from stripping trailing empty lines from $(...),
# which would misalign the subsequent 'read' commands.

# Map the bulk options to variables, providing defaults where empty
{
  read -r key
  read -r history_lines
  read -r editor_open_cmd
  read -r browser_open_cmd
  read -r fzf_path
  read -r fzf_display_options
  read -r path_extension
  read -r loglevel_tmux
  read -r loglevel_file
  read -r log_filename
  read -r python
  read -r python_path
  read -r use_colors
  read -r ls_colors_filename
  read -r user_schemes_path
  read -r hide_fzf_header
  read -r hide_bottom_bar
} <<< "$_bulk_options"

# Apply defaults for empty values
key=${key:-'C-h'}
history_lines=${history_lines:-'0'}
editor_open_cmd=${editor_open_cmd:-"tmux new-window -n 'vim' vim +%line '%file'"}
browser_open_cmd=${browser_open_cmd:-"$browser_open_default"}
fzf_path=${fzf_path:-'fzf'}
fzf_display_options=${fzf_display_options:-'-w 100% --maxnum-displayed 20 --multi --track --no-preview'}
path_extension=${path_extension:-''}
loglevel_tmux=${loglevel_tmux:-'WARNING'}
loglevel_file=${loglevel_file:-'DEBUG'}
log_filename=${log_filename:-''}
python=${python:-'python3'}
python_path=${python_path:-''}
use_colors=${use_colors:-'on'}
ls_colors_filename=${ls_colors_filename:-''}
user_schemes_path=${user_schemes_path:-''}
hide_fzf_header=${hide_fzf_header:-'DEPRECATED'}
hide_bottom_bar=${hide_bottom_bar:-'off'}

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
python_q=$(printf "%q" "$python")
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
if [ ! -x $python_q ]; then
  tmux display-message -d 0 \"fzf-links: no executable python found at: $python\"
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

# End profiling the entire script load time
_prof_end=$EPOCHREALTIME

# Log the total load duration in milliseconds to ~/tmux-fzf-links.log
# Note: This includes the time spent calling `tmux show` for options.
python3 -c "print(f'$(date): Full plugin load took {int(($_prof_end - $_prof_start) * 1000)}ms')" >> ~/tmux-fzf-links.log
