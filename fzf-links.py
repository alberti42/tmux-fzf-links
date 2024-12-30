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

def run_fzf(fzf_options:str,choices:list[str]):
    """Run fzf with the given options."""
    default_options = "-w 100% -h 50% --multi -0 --no-preview"
    options = fzf_options or default_options
    cmd = f"fzf-tmux {options}"
    return subprocess.run(cmd, input="\n".join(choices), shell=True, text=True, capture_output=True).stdout

def open_link(link:str, custom_open_cmd:str):
    """Open a link using the appropriate handler."""
    process: str | None = None
    if custom_open_cmd:
        process = custom_open_cmd
    elif shutil.which("xdg-open"):
        process = "xdg-open"
    elif shutil.which("open"):
        process = "open"
    elif "BROWSER" in os.environ:
        _ = subprocess.Popen([os.environ["BROWSER"], link], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if process:
        _ = subprocess.Popen([process, link], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def trim_str(s:str) -> str:
    """Trim leading and trailing spaces from a string."""
    return s.strip()

def remove_escape_sequences(text:str) -> str:
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
        pre_handler:Callable[[str], str] | None  # A function that takes a string and returns a string
        post_handler: Callable[[str], str] | None  # A function that takes a string and returns a string
        regex: re.Pattern[str]            # A compiled regex pattern

    # Define schemes
    schemes: dict[str, SchemeEntry] = {
        "URL": {"post_handler": identity_handler, "pre_handler": None, "regex": re.compile(r"(?P<link>https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*)")},
        "IP":  {"post_handler": identity_handler, "pre_handler": None, "regex": re.compile(r"(?P<link>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(:[0-9]{1,5})?(/\S+)*)")},
        "GIT": {"post_handler": git_handler, "pre_handler": None, "regex": re.compile(r"(?P<link>(ssh://)?git@\S*)")},
    }

    items:set[str] = set()

    # Process each scheme
    for scheme_type,scheme in schemes.items():
        # Use regex.finditer to iterate over all matches
        for match in scheme['regex'].finditer(content):
            # Extract the match string
            matched_text = match.group("link")  # Group 0 contains the entire match
            if isinstance(matched_text,str):
                if scheme['pre_handler']:
                    matched_text = scheme['pre_handler'](matched_text)
                items.add(scheme_type + "  " + matched_text)

    if not items:
        _ = subprocess.run("tmux display 'tmux-fzf-url-links: no URLs found'", shell=True)
        return

    # Sort items
    sorted_choices = sorted(items)

    # Number the items
    numbered_choices = [f"{idx:3d}  {item}" for idx, item in enumerate(sorted_choices, 1)]

    # Run fzf and get selected items
    selected = run_fzf(fzf_options,numbered_choices)
    if not selected.strip():
        _ = subprocess.run("tmux display 'tmux-fzf-links: no selection made'", shell=True)
        return

    # Regular expression to parse the selected item
    selected_item_pattern = r"\s*(?P<idx>\d+)\s+(?P<type>\S+)\s+(?P<link>.+)"

    # Process selected items
    for selected_item in selected.strip().splitlines():
        selected_item = trim_str(selected_item)
        match = re.match(selected_item_pattern, selected_item)
        if match:
            idx = match.group("idx")
            scheme_type = match.group("type")
            link = match.group("link")

            if not (isinstance(idx,str) and isinstance(scheme_type,str) and isinstance(link,str)):
                _ = subprocess.run(f"tmux display 'tmux-fzf-url-links: malformed selection: {selected_item}'", shell=True)
                return

            post_handler = schemes[scheme_type]["post_handler"]

            if post_handler is None:
                _ = subprocess.run(f"tmux display 'tmux-fzf-url-links: malformed selection: {selected_item}'", shell=True)
                return

            post_handled_link = post_handler(link)

            open_link(post_handled_link, custom_open_cmd)
        else:
            _ = subprocess.run(f"tmux display 'tmux-fzf-url-links: malformed selection: {selected_item}'", shell=True)

if __name__ == "__main__":
    try:
        main(*sys.argv[1:])
    except KeyboardInterrupt:
        _ = subprocess.run("tmux display 'tmux-fzf-links: script interrupted.'", shell=True)
