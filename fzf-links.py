#!/usr/bin/env python3

#===============================================================================
#   Author: (c) 2024 Andrea Alberti
#===============================================================================

import os
import re
import subprocess
import sys
import shlex
import shutil
from enum import Enum
from typing import Callable,TypedDict

class PatternNotMatching(Exception):
    """Raise exception when the pattern does not match a string already matched"""

class NoSuitableAppFound(Exception):
    """Raise exception when no suitable app was found to open the link"""

class FzfError(Exception):
    def __init__(self, message: str, returncode: int) -> None:
        super().__init__(message)
        self.returncode:int = returncode

def git_handler(s:str) -> str:
    return f"https://github.com/{s}"

def error_handler(s:str) -> str:
    # Handle error messages appearing on the command line
    # and create an appropriate link to open the affected file 

    match = schemes["ERROR"]["regex"].search(s)
    if match is None:
        raise PatternNotMatching('unexpectedtly pattern did not match')
    
    file=match.group('file')
    line=match.group('line')

    if not (isinstance(file,str) and isinstance(line,str)):
        raise PatternNotMatching('unexpectedtly pattern did not match')

    return f"{file}:{line}"

class AppType(Enum):
    EDITOR = 0
    BROWSER = 1

# Define the structure of each scheme entry
class SchemeEntry(TypedDict):
    app_type:AppType
    pre_handler:Callable[[str], str] | None  # A function that takes a string and returns a string
    post_handler: Callable[[str], str] | None  # A function that takes a string and returns a string
    regex: re.Pattern[str]            # A compiled regex pattern

# Define schemes
schemes: dict[str, SchemeEntry] = {
    "URL": {"app_type":AppType.BROWSER, "post_handler": None, "pre_handler": None, "regex": re.compile(r"(?P<link>https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*)")},
    "IP":  {"app_type":AppType.BROWSER, "post_handler": None, "pre_handler": None, "regex": re.compile(r"(?P<link>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(:[0-9]{1,5})?(/\S+)*)")},
    "GIT": {"app_type":AppType.BROWSER, "post_handler": git_handler, "pre_handler": None, "regex": re.compile(r"(?P<link>(ssh://)?git@\S*)")},
    "ERROR": {"app_type":AppType.EDITOR, "post_handler": error_handler, "pre_handler": None, "regex": re.compile(r"(?P<link>File \"(?P<file>...*?)\"\, line (?P<line>[0-9]+))")}
}

def run_fzf(fzf_display_options: str, choices: list[str]) -> subprocess.CompletedProcess[str]:
    """Run fzf with the given options."""
    cmd = f"fzf-tmux {fzf_display_options}"
    result = subprocess.run(cmd, input="\n".join(choices), shell=True, text=True, capture_output=True)
    if result.returncode not in [0, 130]:  # Allow exit code 130 for user cancellation
        raise FzfError(f"fzf failed with exit code {result.returncode}: {result.stderr}", result.returncode)
    return result

def open_link(link:str, editor_open_cmd:str, browser_open_cmd:str, app_type:AppType):
    """Open a link using the appropriate handler."""

    process: str | None = None

    if app_type==AppType.EDITOR and editor_open_cmd:
        process = editor_open_cmd
    elif app_type==AppType.BROWSER and browser_open_cmd:
        process = browser_open_cmd
    elif shutil.which("xdg-open"):
        process = "xdg-open"
    elif shutil.which("open"):
        process = "open"
    elif app_type==AppType.EDITOR and "EDITOR" in os.environ:
        process = os.environ["EDITOR"]
    elif app_type==AppType.BROWSER and "BROWSER" in os.environ:
        process = os.environ["BROWSER"]

    if process is None:
        raise NoSuitableAppFound("no suitable app was found to open the link")

    print(f"PROCESS {process}")
    # Build the command
    cmd = f"{process} {shlex.quote(link)}"
    print(cmd)
    try:
        # Run the command and capture stdout and stderr
        proc = subprocess.Popen(
            cmd,
            shell=True,  # Execute in the user's default shell
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,  # Decode output to strings
        )

        # Communicate to capture output and error
        stdout, stderr = proc.communicate()

        # Check for errors or unexpected output
        if proc.returncode != 0:
            raise RuntimeError(f"Command failed with return code {proc.returncode}. Stderr: {stderr}")

        print(f"Command succeeded. Stdout: {stdout}")
    except Exception as e:
        print(f"ERROR {e}")
        raise RuntimeError(f"Failed to execute command '{cmd}': {e}")


def trim_str(s:str) -> str:
    """Trim leading and trailing spaces from a string."""
    return s.strip()

def remove_escape_sequences(text:str) -> str:
    # Regular expression to match ANSI escape sequences
    ansi_escape_pattern = r'\x1B\[[0-9;]*[mK]'
    # Replace escape sequences with an empty string
    return re.sub(ansi_escape_pattern, '', text)

def main(history_limit:str="screen", editor_open_cmd:str='', browser_open_cmd:str='', fzf_display_options:str='', path_extension:str=''):
    # Add extra path if provided
    if path_extension and path_extension not in os.environ["PATH"]:
        os.environ["PATH"] = f"{path_extension}:{os.environ['PATH']}"

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
    try:
        # Run fzf and get selected items
        result = run_fzf(fzf_display_options, numbered_choices)
        
        # Process selected items
        selected = result.stdout.strip().splitlines()

        # Handle normal behavior (130 is the exit code in fzf manual when user interrupts it)
        if result.returncode == 130 or selected == []:
            _ = subprocess.run(["tmux", "display", "tmux-fzf-links: no selection made"], shell=False)
            return        

    except FzfError as e:
        if e.returncode == 130:
            _ = subprocess.run(["tmux", "display", "tmux-fzf-links: selection cancelled (ESC or Ctrl+C)"], shell=False)
        else:
            _ = subprocess.run(["tmux", "display", f"tmux-fzf-links: unexpected error: {e}"], shell=False)

    
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
                _ = subprocess.run(['tmux', 'display', f'tmux-fzf-url-links: malformed selection: {selected_item}'], shell=False)
                return

            post_handler = schemes[scheme_type]["post_handler"]

            if post_handler is None:
                _ = subprocess.run(['tmux', 'display', f'tmux-fzf-url-links: malformed selection: {selected_item}'], shell=False)
                return

            post_handled_link = post_handler(link)
            
            try:
                open_link(post_handled_link, editor_open_cmd, browser_open_cmd, schemes[scheme_type]["app_type"])
            except (NoSuitableAppFound, PatternNotMatching) as e:
                _ = subprocess.run(['tmux', 'display', f'tmux-fzf-links: {e}'], shell=False)
            except Exception as e:
                _ = subprocess.run(['tmux', 'display', f'tmux-fzf-links: unexpected error: {e}'], shell=False)
        else:
            _ = subprocess.run(['tmux', 'display', f'tmux-fzf-url-links: malformed selection: {selected_item}'], shell=False)

if __name__ == "__main__":
    try:
        main(*sys.argv[1:])
    except KeyboardInterrupt:
        _ = subprocess.run("tmux display 'tmux-fzf-links: script interrupted.'", shell=True)
