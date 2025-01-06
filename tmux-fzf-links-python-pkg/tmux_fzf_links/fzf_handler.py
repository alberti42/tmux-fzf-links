#===============================================================================
#   Author: (c) 2024 Andrea Alberti
#===============================================================================

import shlex
from .errors_types import FailedTmuxPaneHeight, FzfError, FzfUserInterrupt
import subprocess
import logging
import tempfile
import os

def extract_option(cmd_user_args:list[str],option:str) -> str | None:
    # get the user option defining the maximum number of matches to be
    # displayed simultaneously in the fzf window

    if option in cmd_user_args:
        # Find the index of '--maxnum-displayed' and get the next argument
        option_index = cmd_user_args.index(option)
        option_arg = cmd_user_args[option_index + 1]

        # Remove `option` and its argument
        cmd_user_args.pop(option_index)  # Remove `option`
        cmd_user_args.pop(option_index)  # Remove the argument (shifts due to first pop)

        return option_arg
        # except (IndexError, ValueError):
        #     # Handle missing or invalid value for '--maxnum-displayed'
        #     raise FailedTmuxPaneHeight("option '--maxnum-displayed' is defined but its value is missing or invalid.")
    else:
        # `option` is not defined
        return None

def run_fzf(fzf_display_options: str, choices: list[str], use_ls_colors: bool) -> str:
    """Run fzf within a tmux popup with the given options and handle output via mkfifo."""

    # Parse user options into a list
    cmd_user_args: list[str] = shlex.split(fzf_display_options)

    # Get the maximum number of matches to be displayed at once
    maxnum_value_str = extract_option(cmd_user_args,'--maxnum-displayed')
    if maxnum_value_str:
        try:
            if maxnum_value_str.endswith('%'):
                # Convert percentage to an integer based on pane_height
                percentage = int(maxnum_value_str[:-1])  # Remove '%' and convert to int

                try:
                    pane_height_str = subprocess.check_output(
                        ('tmux', 'display', '-p', '#{pane_height}',),
                        shell=False,
                        text=True,
                    )
                    pane_height = int(pane_height_str)
                except Exception as e:
                    raise FailedTmuxPaneHeight(f"tmux pane height could not be determined: {e}")
                
                maxnum_value = pane_height * percentage // 100
            else:
                # Convert the argument directly to an integer
                maxnum_value = int(maxnum_value_str)
        except (IndexError, ValueError):
            # Handle missing or invalid value for '--maxnum-displayed'
            raise FailedTmuxPaneHeight("option '--maxnum-displayed' is defined but its value is missing or invalid.")



    # Compute the required height
    height = len(choices)  # Number of lines
    if maxnum_value:
        height = max(min(len(choices), maxnum_value), 1)

    # Adjust height for the fzf border
    fzf_height = height + 4

    # Base fzf arguments
    fzf_args = ['--no-sort']
    if use_ls_colors:
        fzf_args.append('--ansi')

    
    # Combine fzf arguments, giving user options higher priority
    cmd_args = fzf_args + cmd_user_args

    # Create named pipes for stdout and stderr
    stdout_pipe = tempfile.mktemp()
    stderr_pipe = tempfile.mktemp()
    os.mkfifo(stdout_pipe)
    os.mkfifo(stderr_pipe)

    try:
        # Prepare the fzf command to run inside the tmux popup
        fzf_command = f"echo -e \"{chr(10).join(choices)}\" | fzf {' '.join(shlex.quote(arg) for arg in cmd_args)} > {shlex.quote(stdout_pipe)} 2> {shlex.quote(stderr_pipe)}"

        # Command to launch tmux popup
        tmux_popup_command = [
            "tmux", "popup",
            "-E",  # Ensure the command runs interactively
            "-h", f"{fzf_height}",  # Height of the popup
            "-w", "80%",  # Adjust width (default 80%)
            fzf_command
        ]

        # Launch the tmux popup and start reading pipes in parallel
        tmux_process = subprocess.Popen(tmux_popup_command, shell=False)
        with open(stdout_pipe, 'r') as stdout_file, open(stderr_pipe, 'r') as stderr_file:
            stdout = stdout_file.read().strip()
            stderr = stderr_file.read().strip()

        # Wait for the tmux popup to complete
        tmux_process.wait()
        logging.debug(f"RETURN {tmux_process.returncode}")
        # Handle errors or user cancellation
        if tmux_process.returncode == 0:
            return stdout
        elif tmux_process.returncode == 130:
            raise FzfUserInterrupt("User canceled selection.")
        else:
            raise FzfError(f"fzf failed with exit code {tmux_process.returncode}: {stderr}")

    finally:
        # Clean up the named pipes
        for pipe in [stdout_pipe, stderr_pipe]:
            if os.path.exists(pipe):
                os.unlink(pipe)
