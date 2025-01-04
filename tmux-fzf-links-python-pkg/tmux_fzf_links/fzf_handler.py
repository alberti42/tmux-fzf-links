#===============================================================================
#   Author: (c) 2024 Andrea Alberti
#===============================================================================

import shlex
from .errors_types import FailedTmuxPaneHeight, FzfError, FzfUserInterrupt
import subprocess

def get_maxnum_displayed(cmd_user_args:list[str]) -> int | None:
    # get the user option defining the maximum number of matches to be
    # displayed simultaneously in the fzf window

    if '--maxnum-displayed' in cmd_user_args:
        try:
            # Find the index of '--maxnum-displayed' and get the next argument
            maxnum_index = cmd_user_args.index('--maxnum-displayed')
            maxnum_arg = cmd_user_args[maxnum_index + 1]

            # Remove '--maxnum-displayed' and its argument
            cmd_user_args.pop(maxnum_index)  # Remove '--maxnum-displayed'
            cmd_user_args.pop(maxnum_index)  # Remove the argument (shifts due to first pop)

            if maxnum_arg.endswith('%'):
                # Convert percentage to an integer based on pane_height
                percentage = int(maxnum_arg[:-1])  # Remove '%' and convert to int

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
                maxnum_value = int(maxnum_arg)

            return maxnum_value
        except (IndexError, ValueError):
            # Handle missing or invalid value for '--maxnum-displayed'
            raise FailedTmuxPaneHeight("option '--maxnum-displayed' is defined but its value is missing or invalid.")
    else:
        # Parameter '--maxnum-displayed' is not defined
        return None

def run_fzf(fzf_display_options:str,choices: list[str],use_ls_colors:bool) -> subprocess.CompletedProcess[str]:
    """Run fzf with the given options."""

    # Split the options into a list
    cmd_user_args: list[str] = shlex.split(fzf_display_options)

    # Get the maximum number of matches to be displayed at once in the fzf window
    maxnum_value = get_maxnum_displayed(cmd_user_args)

    # Compute the required height
    height=len(choices) # number of lines
    if maxnum_value:
        height=max(min(len(choices),maxnum_value),1)

    # Set a list of default argument, which are computed dynamically
    cmd_default_args = ['-h',f'{height+4:d}','--no-sort']  # extend by 4 lines because of the fzf border
    if use_ls_colors:
        cmd_default_args.append('--ansi')
    
    # In this order, user arguments take priority over default arguments
    cmd_args = ['fzf-tmux'] + cmd_default_args + cmd_user_args

    result = subprocess.run(cmd_args, input="\n".join(choices), shell=False, text=True, capture_output=True)
    if result.returncode == 0:
        return result
    elif result.returncode == 130:
        # Allow exit code 130 for user cancellation; see fzf manual
        raise FzfUserInterrupt()
    else:
        raise FzfError(f"fzf failed with exit code {result.returncode}: {result.stderr}", result.returncode)   
