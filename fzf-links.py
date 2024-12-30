#!/usr/bin/env python3

#===============================================================================
#   Author: (c) 2018 Wenxuan
#   Author: (c) 2024 Andrea Alberti
#===============================================================================

import os
import re
import subprocess
import sys
import shutil
from typing import Callable,TypedDict

def identity_handler(s:str) -> str:
    return s

def git_handler(s:str) -> str:
    return f"https://github.com/{s}"

def run_fzf(fzf_options:str):
    """Run fzf with the given options."""
    default_options = "-w 100% -h 50% --multi -0 --no-preview"
    options = fzf_options or default_options
    cmd = f"fzf-tmux {options}"
    return subprocess.run(cmd, shell=True, text=True, capture_output=True).stdout

def open_link(link:str):
    """Open a link using the appropriate handler."""
    if "BROWSER" in os.environ:
        _ = subprocess.Popen([os.environ["BROWSER"], link], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif shutil.which("xdg-open"):
        _ = subprocess.Popen(["xdg-open", link], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif shutil.which("open"):
        _ = subprocess.Popen(["open", link], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def trim_str(s:str) -> str:
    """Trim leading and trailing spaces from a string."""
    return s.strip()

def remove_escape_sequences(text):
    # Regular expression to match ANSI escape sequences
    ansi_escape_pattern = r'\x1B\[[0-9;]*[mK]'
    # Replace escape sequences with an empty string
    return re.sub(ansi_escape_pattern, '', text)

def main(extra_filter:str='', history_limit:str="screen", custom_open_cmd:str='', fzf_options:str='', extra_path:str=''):
    # Add extra path if provided
    if extra_path and extra_path not in os.environ["PATH"]:
        os.environ["PATH"] = f"{extra_path}:{os.environ['PATH']}"

    # Capture tmux content
    if history_limit == "screen":
        capture_str="tmux capture-pane -J -p -e"
    else:
        capture_str="tmux capture-pane -J -p -e -S -{history_limit}"

    content = subprocess.check_output(
            capture_str,
            shell=True,
            text=True,
        )
    # Remove escape sequences
    content=remove_escape_sequences(content)


    # Define the structure of each scheme entry
    class SchemeEntry(TypedDict):
        handler: Callable[[str], str]  # A function that takes a string and returns a string
        regex: re.Pattern[str]            # A compiled regex pattern

    # Define schemes
    schemes: dict[str, SchemeEntry] = {
        "URL": {"handler": identity_handler, "regex": re.compile(r"(?P<link>https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*)")},
        "IP":  {"handler": identity_handler, "regex": re.compile(r"(?P<link>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(:[0-9]{1,5})?(/\S+)*)")},
        "GIT": {"handler": git_handler, "regex": re.compile(r"(ssh://)?git@(?P<link>\S*)")},
    }

    items:set[str] = set()

    # Process each scheme
    for scheme_type,scheme in schemes.items():
        # Use regex.finditer to iterate over all matches
        for match in scheme['regex'].finditer(content):
            # Extract the match string
            matched_text = match.group("link")  # Group 0 contains the entire match
            if isinstance(matched_text,str):
                items.add(scheme_type + "  " + scheme["handler"](matched_text))

    if not items:
        _ = subprocess.run("tmux display 'tmux-fzf-url-links: no URLs found'", shell=True)
        return

    # Sort items
    sorted_items = sorted(items)

    # Number the items
    numbered_items = [f"{idx:3d}  {item}" for idx, item in enumerate(sorted_items, 1)]

    # Run fzf and get selected items
    selected = run_fzf(fzf_options="\n".join(numbered_items))
    if not selected.strip():
        _ = subprocess.run("tmux display 'tmux-fzf-url+: no selection made'", shell=True)
        return

    # Process selected items
    for selected_item in selected.strip().splitlines():
        selected_item = trim_str(selected_item)
        parts = selected_item.split("  ", 2)  # Split into 3 parts: index, type, and link
        if len(parts) == 3:
            _, type_, link = parts
            open_link(link)
        else:
            print(f"Malformed selection: {selected_item}", file=sys.stderr)

if __name__ == "__main__":
    try:
        main(*sys.argv[1:])
    except KeyboardInterrupt:
        subprocess.run("tmux display 'Script interrupted.'", shell=True)
