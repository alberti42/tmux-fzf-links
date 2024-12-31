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

class CommandFailed(Exception):
    """Raise exception when the executed app exits with a nonzero return code"""

class FzfUserInterrupt(Exception):
    """Raise exception when the user cancels fzf modal window"""

class FzfError(Exception):
    """Raise exception when fzf fails"""
    def __init__(self, message: str, returncode: int) -> None:
        super().__init__(message)
        self.returncode:int = returncode

def git_handler(match:re.Match[str]) -> str:
    return f"https://github.com/{match.group(0)}"

def error_handler(match:re.Match[str]) -> str:
    # Handle error messages appearing on the command line
    # and create an appropriate link to open the affected file 
    
    file=match.group('file')
    line=match.group('line')

    return f"{file}:{line}"

class AppType(Enum):
    EDITOR = 0
    BROWSER = 1

# Define the structure of each scheme entry
class SchemeEntry(TypedDict):
    app_type:AppType
    pre_handler:Callable[[re.Match[str]], str] | None  # A function that takes a string and returns a string
    post_handler: Callable[[re.Match[str]], str] | None  # A function that takes a string and returns a string
    regex: re.Pattern[str]            # A compiled regex pattern

# Define schemes
schemes: dict[str, SchemeEntry] = {
    # One can use group names as done in the scheme ERROR to extract subblocks, which are availble to the pre_handler and post_handler
    "URL": {
        "app_type": AppType.BROWSER,
        "post_handler": None,
        "pre_handler": None, "regex": re.compile(r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*")
        },
    "IP": {
        "app_type": AppType.BROWSER,
        "post_handler": None,
        "pre_handler": None, "regex": re.compile(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(:[0-9]{1,5})?(/\S+)*")
        },
    "GIT": {
        "app_type":AppType.BROWSER,
        "post_handler": git_handler,
        "pre_handler": None,
        "regex": re.compile(r"(ssh://)?git@\S*")
        },
    "ERROR": {
        "app_type": AppType.EDITOR,
        "post_handler": error_handler,
        "pre_handler": None, "regex": re.compile(r"File \"(?P<file>...*?)\"\, line (?P<line>[0-9]+)")
        }
    }

def run_fzf(fzf_display_options: str, choices: list[str]) -> subprocess.CompletedProcess[str]:
    """Run fzf with the given options."""
    # Split the options into a list
    cmd_plus_args: list[str] = shlex.split(fzf_display_options)

    # Add 'fzf-tmux' as the first element
    cmd_plus_args.insert(0, 'fzf-tmux')

    result = subprocess.run(cmd_plus_args, input="\n".join(choices), shell=True, text=True, capture_output=True)
    if result.returncode == 0:
        return result
    elif result.returncode == 130:
        # Allow exit code 130 for user cancellation; see fzf manual
        raise FzfUserInterrupt()
    else:
        raise FzfError(f"fzf failed with exit code {result.returncode}: {result.stderr}", result.returncode)

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

    # Build the command
    
    # Split the options into a list
    cmd_plus_args: list[str] = shlex.split(link)

    # Add '{process}' as the first element
    cmd_plus_args.insert(0, process)
    
    try:
        # Run the command and capture stdout and stderr
        proc = subprocess.Popen(
            cmd_plus_args,
            shell=False,  # Execute in the user's default shell
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,  # Decode output to strings
        )

        # Communicate to capture output and error
        _, stderr = proc.communicate()

        # Check for errors or unexpected output
        if proc.returncode != 0:
            raise CommandFailed(f"return code {proc.returncode}: {stderr.decode('utf-8')}")

    except Exception as e:
        raise CommandFailed(f"failed to execute command '{" ".join(cmd_plus_args)}': {e}")


def trim_str(s:str) -> str:
    """Trim leading and trailing spaces from a string."""
    return s.strip()

def remove_escape_sequences(text:str) -> str:
    # Regular expression to match ANSI escape sequences
    ansi_escape_pattern = r'\x1B\[[0-9;]*[mK]'
    # Replace escape sequences with an empty string
    return re.sub(ansi_escape_pattern, '', text)

def main(history_limit:str='', editor_open_cmd:str='', browser_open_cmd:str='', fzf_display_options:str='', path_extension:str='', verbose:str=''):
    # Add extra path if provided
    if path_extension and path_extension not in os.environ["PATH"]:
        os.environ["PATH"] = f"{path_extension}:{os.environ['PATH']}"
    
    verbose_status:bool=False
    if verbose=='on':
        verbose_status=True

    # Capture tmux content
    capture_str:list[str]=['tmux', 'capture-pane', '-J', '-p', '-e']
    
    if history_limit != "screen":
        # It the history limit is not set to screen, then so many extra
        # lines are captured from the buffer history
        capture_str.extend(['-S', f'-{history_limit}'])
    
    content = subprocess.check_output(
            capture_str,
            shell=False,
            text=True,
        )

    # Remove escape sequences
    content=remove_escape_sequences(content)

    # We use the unique set as an expedient to sort over
    # pre_handled_text while keeping the original text
    seen:set[str] = set()
    items:list[tuple[str,str]] = []
    
    max_len_scheme_names:int = max([len(scheme) for scheme in schemes.keys()])

    # Process each scheme
    for scheme_type,scheme in schemes.items():
        # Use regex.finditer to iterate over all matches
        for match in scheme['regex'].finditer(content):
            # Extract the match string
            matched_text = match.group(0)  # Group 0 contains the entire match
            if scheme['pre_handler']:
                pre_handled_text = scheme['pre_handler'](match)
            else:
                pre_handled_text = matched_text
            if matched_text not in seen:
                seen.add(matched_text)
                # We justify the scheme name for prettier print
                justified_scheme_type=scheme_type.ljust(max_len_scheme_names)
                # We keep a copy of the original matched text for later
                items.append((justified_scheme_type + "  " + pre_handled_text,matched_text,))
    # Clean up no longer needed variables
    del seen
    
    if items == []:
        if verbose_status:
            _ = subprocess.run(['tmux', 'display', 'tmux-fzf-url-links: no link found'], shell=False)
        return

    # Sort items
    sorted_choices = sorted(items, key=lambda x: x[0])

    # Number the items
    numbered_choices = [f"{idx:3d}  {item[0]}" for idx, item in enumerate(sorted_choices, 1)]
    
    # Run fzf and get selected items
    try:
        # Run fzf and get selected items
        result = run_fzf(fzf_display_options, numbered_choices)
    except FzfError as e:
        _ = subprocess.run(["tmux", "display", f"tmux-fzf-links: unexpected error: {e}"], shell=False)
        return
    except FzfUserInterrupt as e:
        if verbose_status == True:
            _ = subprocess.run(["tmux", "display", "tmux-fzf-links: no selection made"], shell=False)
        return
    
    # Process selected items
    selected_choices = result.stdout.splitlines()

    # Regular expression to parse the selected item from the fzf options
    # Each line is in the format {three-digit number, space, space, 
    selected_item_pattern = r"\s*(?P<idx>\d+)\s+(?P<type>\S+)\s+(?P<link>.+)"

    # Process selected items
    for selected_choice in selected_choices:
        match = re.match(selected_item_pattern, selected_choice)
        if match:
            idx_str:str = match.group("idx")
            scheme_type:str = match.group("type")
            
            try:
                idx:int=int(idx_str,10)
                # pick the original item to be searched again
                # before passing the `match` object to the post handler
                selected_item=sorted_choices[idx-1][1]
            except:
                _ = subprocess.run(['tmux', 'display', f'tmux-fzf-url-links: malformed selection: {selected_choice}'], shell=False)
                continue
            
            scheme = schemes.get(scheme_type,None)
            
            if scheme is None:
                _ = subprocess.run(['tmux', 'display', f'tmux-fzf-url-links: malformed selection: {selected_choice}'], shell=False)
                continue

            match=scheme["regex"].search(selected_item)
            if match is None:
                _ = subprocess.run(['tmux', 'display', f'unexpectedtly pattern did not match'], shell=False)
                continue          
      
            # Get the post_handler, which applies after the user selection
            post_handler = scheme.get("post_handler",None)

            # Process the match with the post handler
            if post_handler:
                post_handled_link = post_handler(match)    
            else:
                post_handled_link = match.group(0)
            
            try:
                open_link(post_handled_link, editor_open_cmd, browser_open_cmd, schemes[scheme_type]["app_type"])
            except (NoSuitableAppFound, PatternNotMatching, CommandFailed) as e:
                _ = subprocess.run(['tmux', 'display', f'tmux-fzf-links: {e}'], shell=False)
            except Exception as e:
                _ = subprocess.run(['tmux', 'display', f'tmux-fzf-links: unexpectedddd error: {e}'], shell=False)
        else:
            _ = subprocess.run(['tmux', 'display', f'tmux-fzf-url-links: malformed selection: {selected_choice}'], shell=False)

if __name__ == "__main__":
    try:
        main(*sys.argv[1:])
    except KeyboardInterrupt:
        _ = subprocess.run(['tmux', 'display', 'tmux-fzf-links: script interrupted.'], shell=False)
