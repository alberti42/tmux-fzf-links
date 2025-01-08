#===============================================================================
#   Author: (c) 2024 Andrea Alberti
#===============================================================================

import shlex
import subprocess
import tempfile
import os
import sys
from typing import TypedDict

from .errors_types import FailedTmuxPaneSize, FzfError, FzfUserInterrupt

class FzfReturnType(TypedDict):
    selection:list[str]
    pressed_key:str

def extract_option(cmd_user_args:list[str],option:str) -> str | None:
    # extract the user option

    if option in cmd_user_args:
        # Find the index of `option` and get the next argument
        option_index = cmd_user_args.index(option)
        option_arg = cmd_user_args[option_index + 1]

        # Remove `option` and its argument
        cmd_user_args.pop(option_index)  # Remove `option`
        cmd_user_args.pop(option_index)  # Remove the argument (shifts due to first pop)

        return option_arg
    else:
        # `option` is not defined
        return None

def parse_int_option(option_arg:str|None,ref_value:int|None) -> int|None:
    if option_arg is None:
        return None

    if ref_value and option_arg.endswith('%'):
        # Convert percentage to an integer based on the reference value
        percentage = int(option_arg[:-1])  # Remove '%' and convert to int
        int_value = ref_value * percentage // 100
    else:
        # Convert the argument directly to an integer
        int_value = int(option_arg)

    return int_value


def run_fzf(fzf_display_options: str, choices: list[str], use_ls_colors: bool) -> FzfReturnType:
    """Run fzf within a tmux popup with the given options and handle output via mkfifo."""

    # Parse user options into a list
    cmd_user_args: list[str] = shlex.split(fzf_display_options)

    VER_BORDER = 4 # number of characters taken by vertical border
    HOR_BORDER = 2 # number of characters taken by horizontal border

    # Command to launch tmux popup
    tmux_popup_command:list[str] = [
        "tmux", "popup",
        "-E",  # Ensure the command runs interactively
    ]

    # Retrieve the current pane size
    try:
        pane_size_str:str = subprocess.check_output(
            ('tmux', 'display', '-p', '#{pane_height},#{pane_width}',),
            shell=False,
            text=True,
        )
        pane_height, pane_width = map(int, pane_size_str.split(','))
    except Exception as e:
        raise FailedTmuxPaneSize(f"tmux pane size could not be determined: {e}")

    # Set the x offset of the popup
    try:
        x_str = extract_option(cmd_user_args,'-x')
        x = parse_int_option(x_str,None)
    except (IndexError, ValueError):
        raise FailedTmuxPaneSize("option '-x' is defined but its value is missing or invalid")
    if x:
        tmux_popup_command.extend(["-x", f"{x}"])

    # Set the y offset of the popup
    try:
        y_str = extract_option(cmd_user_args,'-y')
        y = parse_int_option(y_str,None)
    except (IndexError, ValueError):
        raise FailedTmuxPaneSize("option '-y' is defined but its value is missing or invalid")
    if y:
        tmux_popup_command.extend(["-y", f"{y}"])

    # Set the width of the popup
    try:
        width_str = extract_option(cmd_user_args,'-w')
        width = parse_int_option(width_str,pane_width-HOR_BORDER)
    except (IndexError, ValueError):
        raise FailedTmuxPaneSize("option '-w' is defined but its value is missing or invalid")
    if width:
        # Force at least one char
        width = max(width,1)

        # Adjust width for the fzf border
        fzf_width = min(width + HOR_BORDER,pane_width)
        tmux_popup_command.extend(["-w", f"{fzf_width}"])

    # Get the height of the popup
    try:
        height_str = extract_option(cmd_user_args,'-h')
        height = parse_int_option(height_str,pane_height-VER_BORDER)
    except (IndexError, ValueError):
        raise FailedTmuxPaneSize("option '-h' is defined but its value is missing or invalid")
    
    if height:
        # Force at least one line
        height = max(height,1)
    else:
        # If height is not specified in the options, the plugin dynamically
        # computes the necessary popup height to fit all items
        height = len(choices)  # Number of lines

    # Get the maximum number of matches to be displayed at once
    try:
        maxnum_str = extract_option(cmd_user_args,'--maxnum-displayed')
        maxnum = parse_int_option(maxnum_str,pane_height-VER_BORDER)
    except (IndexError, ValueError):
        raise FailedTmuxPaneSize("option '--maxnum-displayed' is defined but its value is missing or invalid")
    if maxnum:
        height = min(height,maxnum)

    # Adjust height for the fzf border
    fzf_height = min(height + VER_BORDER,pane_height)
    tmux_popup_command.extend(["-h", f"{fzf_height}"])

    # Base fzf arguments
    fzf_args = ['--no-sort','--bind','alt-enter:print(META-ENTER)+accept',  '--bind', 'enter:print(ENTER)+accept']
    if use_ls_colors:
        fzf_args.append('--ansi')
    
    with_header = False
    if with_header:
        if sys.platform == "darwin":            
            meta_key = "⌥" # option key
        elif sys.platform == "win32":
            meta_key = "alt" # symbol: ⎇
        else:
            # historically the alt key was called meta in unix/linux systems
            meta_key = "meta"  # symbol: ◆ 

        fzf_args.extend(['--header',f"Press {meta_key}+↵ to copy selection to tmux buffer"])

    
    # Combine fzf arguments, giving user options higher priority
    cmd_args = fzf_args + cmd_user_args

    # Create a temporary directory for the named pipes
    with tempfile.TemporaryDirectory() as tmpdir:
        # Paths for the named pipes
        stdout_pipe = os.path.join(tmpdir, 'fzf_stdout')
        stderr_pipe = os.path.join(tmpdir, 'fzf_stderr')

        # Create named pipes for stdout and stderr
        os.mkfifo(stdout_pipe)
        os.mkfifo(stderr_pipe)

        # Choices → [stdin] → fzf (interactive UI on /dev/tty)
        #           → [stdout] → Named Pipe (stdout_pipe)
        #           → [stderr] → Named Pipe (stderr_pipe)
        
        # Prepare the fzf command to run inside the tmux popup
        fzf_command = (
            f"echo \"{chr(10).join(choices)}\" | "
            f"fzf {' '.join(shlex.quote(arg) for arg in cmd_args)} "
            f"> {shlex.quote(stdout_pipe)} 2> {shlex.quote(stderr_pipe)}"
        )

        tmux_popup_command.append(fzf_command)

        try:
            # Start the tmux popup process
            tmux_process = subprocess.Popen(tmux_popup_command, shell=False)

            # Open the named pipes for reading
            with open(stdout_pipe, 'r') as stdout_file, open(stderr_pipe, 'r') as stderr_file:
                # Read stdout and stderr in parallel
                stdout = stdout_file.read().strip()
                stderr = stderr_file.read().strip()

            # Wait for the tmux popup to complete
            tmux_process.wait()

            # Handle errors or user cancellation
            if tmux_process.returncode == 0:

                # Split the lines from fzf
                results = stdout.splitlines()

                # The first line is special and tells us what key was pressed by the user
                pressed_key = results[0]

                return {"pressed_key":pressed_key, "selection":results[1:]}
            elif tmux_process.returncode == 130:
                raise FzfUserInterrupt("User canceled selection.")
            else:
                raise FzfError(f"fzf failed with exit code {tmux_process.returncode}: {stderr}")

        finally:
            # Named pipes are automatically cleaned up with the TemporaryDirectory
            pass

