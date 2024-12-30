#!/usr/bin/env zsh

# To ensure safe execution on all zsh systems
emulate -LR zsh

run_fzf() {
  local fzf_options fzf_default_options
  
  fzf_default_options='-w 100% -h 50% --multi -0 --no-preview'
  fzf_options="${1:-$fzf_default_options}"
  
  eval "fzf-tmux ${fzf_options}"
}

open_url() {
  local custom_open_cmd chosen_url
  custom_open_cmd=$1
  chosen_url=$2

  if [[ -n "$custom_open" ]]; then 
      $custom_open "$chosen_url"
  elif hash xdg-open &>/dev/null; then
      nohup xdg-open "$chosen_url"
  elif hash open &>/dev/null; then
      nohup open "$chosen_url"
  elif [[ -n $BROWSER ]]; then
      nohup "$BROWSER" "$chosen_url"
  fi
}

main() {
  local extra_filter history_limit custom_open_cmd extra_path

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
  
  if [[ $history_limit == "screen" ]]; then
    content="$(tmux capture-pane -J -p -e | sed -r 's/\x1B\[[0-9;]*[mK]//g'))"
  else
    content="$(tmux capture-pane -J -p -e -S -"$history_limit" | sed -r 's/\x1B\[[0-9;]*[mK]//g'))"
  fi

  typeset -a schemes
  
  # URLs
  schemes+=($(echo "$content" | grep -oE '(https?|ftp|file):/?//[-A-Za-z0-9+&@#/%?=~_|!:,.;]*[-A-Za-z0-9+&@#/%=~_|]'))
  
  # WWWs
  schemes+=($(echo "$content" | grep -oE '(http?s://)?www\.[a-zA-Z](-?[a-zA-Z0-9])+\.[a-zA-Z]{2,}(/\S+)*' | grep -vE '^https?://' |sed 's/^\(.*\)$/http:\/\/\1/'))
  
  # ips
  schemes+=($(echo "$content"  | grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(:[0-9]{1,5})?(/\S+)*' |sed 's/^\(.*\)$/http:\/\/\1/'))
  
  # gits
  schemes+=($(echo "$content" | grep -oE '(ssh://)?git@\S*' | sed 's/:/\//g' | sed 's/^\(ssh\/\/\/\)\{0,1\}git@\(.*\)$/https:\/\/\2/'))
  
  # gh
  schemes+=($(echo "$content"   | grep -oE "['\"]([_A-Za-z0-9-]*/[_.A-Za-z0-9-]*)['\"]" | sed "s/['\"]//g" | sed 's#.#https://github.com/&#'))

  items=$(printf '%s\n' "${schemes[@]}" |
    grep -v '^$' |  # Remove empty lines
    sort -u |       # Sort and remove duplicates
    nl -w3 -s '  '  # Number the lines with 3-digit width
  )

  [ -z "$items" ] && tmux display 'tmux-fzf-url: no URLs found' && exit

  echo "$items" | run_fzf "$fzf_options" | awk '{print $2}' | \
  while read -r chosen_url; do
      open_url "$custom_open_cmd" "$chosen_url"
  done
}

trap 'unfunction main run_fzf open_url' EXIT
trap 'echo "Script interrupted or exited abnormally" >&2; unfunction main run_fzf open_url; exit 1' INT

main "$@"
