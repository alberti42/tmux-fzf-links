#===============================================================================
#   Author: (c) 2024 Andrea Alberti
#===============================================================================

import shutil
import re
import os
import subprocess
from enum import Enum
from typing import Callable,TypedDict
import shlex

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

PostHandledMatch = dict[str, str] | list[str]

# Define the structure of each scheme entry
class SchemeEntry(TypedDict):
    tags: tuple[str,...]
    opener: OpenerType
    pre_handler: Callable[[re.Match[str]], PreHandledMatch | None] | None  # A function that takes a string and returns a string
    post_handler: Callable[[re.Match[str]], PostHandledMatch] | None  # A function that takes a string and returns a string
    regex: re.Pattern[str]            # A compiled regex pattern

def open_link(editor_open_cmd:str, browser_open_cmd:str, post_handled_match:PostHandledMatch, opener:OpenerType):
    """Open a link using the appropriate handler."""

    # contains the arguments for subprocess.Popen, including the process to start
    args:list[str]

    if opener == OpenerType.CUSTOM:
        if isinstance(post_handled_match,dict):
            raise RuntimeError("'post_handled_match' is of type 'dict' whereas a type 'list' was expected")     
        args = post_handled_match
    else:
        if isinstance(post_handled_match,list):
            raise RuntimeError("'post_handled_match' is of type 'list' whereas a type 'dict' was expected")     

        # template with the command to be executed
        template:str

        if opener==OpenerType.EDITOR and editor_open_cmd:
            template = editor_open_cmd
        elif opener==OpenerType.BROWSER and browser_open_cmd:
            template = browser_open_cmd
        elif shutil.which("xdg-open"):
            template = "xdg-open '%%file'"
        elif shutil.which("open"):
            template = "open '%%file'"
        elif opener==OpenerType.EDITOR and "EDITOR" in os.environ:
            template = f"{os.environ["EDITOR"]} '%%file'"
        elif opener==OpenerType.BROWSER and "BROWSER" in os.environ:
            template = f"{os.environ["BROWSER"]} '%%file'"
        else:
            raise NoSuitableAppFound("no suitable app was found to open the link")

        # The keys in the dictionary represent the placeholders
        # to be replaced in the template with the corresponding values
        cmd = template
        for key,value in post_handled_match.items():
            cmd = cmd.replace(f"%{key}",value)

        args = shlex.split(cmd)

    try:
        # Run the command and capture stdout and stderr
        proc = subprocess.Popen(
            args,
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
