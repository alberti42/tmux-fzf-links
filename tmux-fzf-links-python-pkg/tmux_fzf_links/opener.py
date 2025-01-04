#===============================================================================
#   Author: (c) 2024 Andrea Alberti
#===============================================================================

import shutil
import re
import os
import subprocess
from enum import Enum
from typing import Callable,TypedDict

from .errors_types import CommandFailed, NoSuitableAppFound

class OpenerType(Enum):
    EDITOR = 0
    BROWSER = 1
    # when set to custom, the post_handler is responsible to
    # provide the opener as first element of the list
    CUSTOM = 2 

class PreHandledMatch(TypedDict):
    display_text: str
    tag: str

# Define the structure of each scheme entry
class SchemeEntry(TypedDict):
    tags: tuple[str,...]
    opener: OpenerType
    pre_handler: Callable[[re.Match[str]], PreHandledMatch | None] | None  # A function that takes a string and returns a string
    post_handler: Callable[[re.Match[str]], tuple[str,...]] | None  # A function that takes a string and returns a string
    regex: re.Pattern[str]            # A compiled regex pattern

def open_link(editor_open_cmd:str, browser_open_cmd:str, post_handled_match:tuple[str,...], opener:OpenerType|str):
    """Open a link using the appropriate handler."""

    process: str | None = None

    if opener==OpenerType.EDITOR and editor_open_cmd:
        process = editor_open_cmd
    elif opener==OpenerType.BROWSER and browser_open_cmd:
        process = browser_open_cmd
    elif opener==OpenerType.CUSTOM:
        process = None
    elif shutil.which("xdg-open"):
        process = "xdg-open"
    elif shutil.which("open"):
        process = "open"
    elif opener==OpenerType.EDITOR and "EDITOR" in os.environ:
        process = os.environ["EDITOR"]
    elif opener==OpenerType.BROWSER and "BROWSER" in os.environ:
        process = os.environ["BROWSER"]
    else:
        raise NoSuitableAppFound("no suitable app was found to open the link")

    # Build the command
    
    # Add '{process}' as the first element
    cmds = list(post_handled_match)
    if process:
        cmds.insert(0, process)
    
    try:
        # Run the command and capture stdout and stderr
        proc = subprocess.Popen(
            cmds,
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
        raise CommandFailed(f"failed to execute command '{" ".join(post_handled_match)}': {e}")
