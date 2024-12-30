#!/usr/bin/env zsh

#===============================================================================
#   Author: (c) 2018 Wenxuan
#   Author: (c) 2024 Andrea Alberti
#===============================================================================

# To ensure safe execution on all zsh systems
emulate -LR zsh

run_fzf() {
  local fzf_default_options fzf_options
  fzf_default_options='-w 100% -h 50% --multi -0 --no-preview'
  fzf_options="${1:-$fzf_default_options}"
  
  # Splits the string with options into an array based on whitespace
  fzf-tmux ${(z)fzf_options}
}

open_link() {
  local custom_open_cmd chosen_link
  custom_open_cmd=$1
  chosen_link=$2

  if [[ -n "$custom_open" ]]; then 
      $custom_open "$chosen_link"
  elif command -v xdg-open > /dev/null; then
      nohup xdg-open "$chosen_link"
  elif command -v open > /dev/null; then
      nohup open "$chosen_link"
  elif [[ -n $BROWSER ]]; then
      nohup "$BROWSER" "$chosen_link"
  fi
}

trim_str() {
    local s=$1 LC_CTYPE=C
    s=${s#"${s%%[![:space:]]*}"}
    s=${s%"${s##*[![:space:]]}"}
    printf '%s' "$s"
}

main() {
  local extra_filter history_limit custom_open_cmd fzf_options extra_path

  extra_filter="$1"
  history_limit="$2"
  custom_open_cmd="$3"
  fzf_options="$4"
  extra_path="$5"

  # Add extra path if provided
  if [[ -n $extra_path ]]; then
    if [[ ":$PATH:" != *":$extra_path:"* ]]; then
      export PATH="$extra_path${PATH:+:${PATH}}"
    fi
  fi

  local content
  
  history_limit="screen"
  if [[ $history_limit == "screen" ]]; then
    content="$(tmux capture-pane -J -p -e | sed -r 's/\x1B\[[0-9;]*[mK]//g'))"
  else
    content="$(tmux capture-pane -J -p -e -S -"$history_limit" | sed -r 's/\x1B\[[0-9;]*[mK]//g'))"
  fi

  local schemes items sorted_items numbered_items
  typeset -A schemes
  typeset -U items
  typeset -a sorted_items numbered_items
  
  # Define schemes
  schemes[URL]="grep -oE '(https?|ftp|file):/?//[-A-Za-z0-9+&@#/%?=~_|!:,.;]*[-A-Za-z0-9+&@#/%=~_|]'"
  
  schemes[WWW]="grep -oE '(http?s://)?www\.[a-zA-Z](-?[a-zA-Z0-9])+\.[a-zA-Z]{2,}(/\S+)*' | grep -vE '^https?://' | sed 's/^\(.*\)$/http:\/\/\1/'"
  
  schemes[IP]="grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(:[0-9]{1,5})?(/\S+)*' | sed 's/^\(.*\)$/http:\/\/\1/'"
  
  schemes[GIT]="grep -oE '(ssh://)?git@\S*' | sed 's/:/\//g' | sed 's/^\(ssh\/\/\/\)\{0,1\}git@\(.*\)$/https:\/\/\2/'"
  
  local scheme type match

  # Process each scheme
  for type in "${(@k)schemes}"; do
    scheme=${schemes[$type]}
    
    # Run the command to find matches
    matches=$(echo "$content" | eval $scheme)

    for match in ${(f)matches}; do
      # Store as "type | match | handler"
      items+=("$type  $match")
    done
  done
  
  # Display the unique items in tmux
  [[ -z "$items" ]] && tmux display 'tmux-fzf-url+: no URLs found' && exit 0

  # Sort the array
  sorted_items=("${(on)items[@]}")
  
  # Add a number to each item
  numbered_items=()
  
  idx=1
  for item in $sorted_items; do    
    # Format the index as right-aligned with 3 digits
    formatted_idx=$(printf "%3d" "$idx")
    numbered_items+=("$formatted_idx  $item")
    idx=$((idx + 1))  # Increment the index
  done

  # Combine items and pass to fzf
  selected_items=$(printf '%s\n' "${numbered_items[@]}" | run_fzf "$fzf_options")

  local remaining link

  if [[ -n "$selected_items" ]]; then
    # Iterate through each selected line
    while IFS= read -r selected_item; do
      # Trim leading and trailing spaces
      selected_item=$(trim_str "$selected_item")
      
      # Split into components
      index=${selected_item%% *}                          # First part (index)
      remaining=${selected_item#*  }                      # Remove the index
      type=${remaining%%  *}                               # Extract the type
      link=${remaining#*  }                                # Extract the link

      # Open link with appropriate handler
      open_link "$link"
    done <<< "$selected_items"
  else
    tmux display 'tmux-fzf-url+: no selection made' && exit 0
  fi
}

trap 'unfunction main run_fzf open_url trim_str' EXIT
trap 'tmux display-message "Script interrupted or exited abnormally" >&2; unfunction main run_fzf open_url trim_str; exit 1' INT

main "$@"
