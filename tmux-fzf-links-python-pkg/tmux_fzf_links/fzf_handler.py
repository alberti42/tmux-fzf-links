import shlex
from .errors_types import FailedTmuxPaneHeight, FzfError, FzfUserInterrupt
import subprocess

def get_max_h_value(cmd_user_args:list[str]) -> int | None:
    if '-max-h' in cmd_user_args:
        try:
            # Find the index of '-max-h' and get the next argument
            max_h_index = cmd_user_args.index('-max-h')
            max_h_arg = cmd_user_args[max_h_index + 1]

            # Remove '-max-h' and its argument
            cmd_user_args.pop(max_h_index)  # Remove '-max-h'
            cmd_user_args.pop(max_h_index)  # Remove the argument (shifts due to first pop)

            if max_h_arg.endswith('%'):
                # Convert percentage to an integer based on pane_height
                percentage = int(max_h_arg[:-1])  # Remove '%' and convert to int

                try:
                    pane_height_str = subprocess.check_output(
                        ('tmux', 'display', '-p', '#{pane_height}',),
                        shell=False,
                        text=True,
                    )
                    pane_height = int(pane_height_str)
                except Exception as e:
                    raise FailedTmuxPaneHeight(f"tmux pane height could not be determined: {e}")
                
                max_h_value = pane_height * percentage // 100
            else:
                # Convert the argument directly to an integer
                max_h_value = int(max_h_arg)

            return max_h_value
        except (IndexError, ValueError):
            # Handle missing or invalid value for '-max-h'
            raise FailedTmuxPaneHeight("option '-max-h' is defined but its value is missing or invalid.")
    else:
        # Parameter '-max-h' is not defined
        return None

def run_fzf(fzf_display_options:str,choices: list[str],use_ls_colors:bool) -> subprocess.CompletedProcess[str]:
    """Run fzf with the given options."""

    # Split the options into a list
    cmd_user_args: list[str] = shlex.split(fzf_display_options)
    max_h_value = get_max_h_value(cmd_user_args)

    # Compute the required height
    height=len(choices)+4 # number of lines
    if max_h_value:
        height=max(min(height,max_h_value),5)
    
    # Set a list of default argument, which are computed dynamically
    cmd_default_args = ['-h',f'{height:d}','--no-sort']
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
