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
import logging
import importlib.util
import pathlib
from typing import override

from .export import OpenerType, SchemeEntry
from .default_schemes import default_schemes

class FailedChDir(Exception):
    """Raise exception when changing directory to tmux pane current directory fails"""

class FailedTmuxPaneHeight(Exception):
    """Raise exception when tmux pane height cannot be determined"""

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

def set_up_logger(loglevel_tmux:str,loglevel_file:str,log_filename:str) -> logging.Logger:

    # Set up the root logger; note: if you decide to create a child logger
    # the root logger level needs to be configured to allow for messages
    # to pass through.
    logger = logging.getLogger()  # root logger when no argument is provided
    # Allow all log messages to pass through; we control the level using handlers
    logger.setLevel(0)

    # Set up tmux log handler
    tmux_handler = setup_tmux_log_handler()
    tmux_handler.setLevel(validate_log_level(loglevel_tmux))
    logger.addHandler(tmux_handler)
    
    if log_filename:
        # Set up file log handler in a safe way where it checks whether
        # the file is writable; if not, the error is reported over tmux display 
        try:
            file_handler = setup_file_log_handler(log_filename)
            file_handler.setLevel(validate_log_level(loglevel_file))
            logger.addHandler(file_handler)
            init_msg="fzf-links tmux plugin started"
            # Send an initialization message to the file handler only
            file_handler.handle(logging.LogRecord(
                    name=logger.name,
                    level=logging.INFO,
                    pathname=__file__,
                    lineno=0,
                    msg=init_msg,
                    args=None,
                    exc_info=None,
                ))
        except Exception as e:
            # To be safe, remove the handler if it was added
            for handler in logger.handlers:
                if isinstance(handler,logging.FileHandler):
                    logger.removeHandler(handler)
                
            # Set level to zero to make sure that the error is displayed 
            tmux_handler.setLevel(0)
            # Log the error to tmux display and exit 
            logger.error(f"error logging to logfile: {log_filename}")
            sys.exit(1)

    return logger

# >>> LOGGER >>>

class TmuxDisplayHandler(logging.Handler):
    @override
    def emit(self, record:logging.LogRecord):
        # Format the log message
        message = self.format(record)
        try:
            # Determine the display command options based on the log level
            display_options = ["tmux", "display-message"]
            if record.levelno >= logging.WARNING:
                display_options.extend(["-d", "0"])  # Pause the message for warnings and errors

            # Include the message
            display_options.append(message)

            # Use tmux display-message to show the log
            _ = subprocess.run(
                display_options,
                check=True,
                shell=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            # Fallback to console if tmux command fails
            print(f"Failed to display message in tmux: {e}")

def setup_tmux_log_handler() -> TmuxDisplayHandler:

    # === Set up tmux logger ===
    
    # Create and add the TmuxDisplayHandler
    tmux_handler = TmuxDisplayHandler()
    # formatter = logging.Formatter("%(levelname)s: %(message)s")
    formatter = logging.Formatter("fzf-links: %(message)s")
    tmux_handler.setFormatter(formatter)

    return tmux_handler

def setup_file_log_handler(log_filename:str='') -> logging.FileHandler:

    # === Set up file logger ===

    # Configure file log handler and check that the logfile can be written
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    
    return file_handler

def validate_log_level(user_level:str):
    """
    Validates the user-provided log level.
    Falls back to WARNING if the level is invalid.

    Args:
        user_level (str): The log level provided by the user (e.g., 'DEBUG', 'INFO').

    Returns:
        int: A valid logging level.
    """
    # Use the internal mapping of log level names to numeric values
    level_mapping = logging._nameToLevel

    # Convert user input to uppercase for case-insensitive matching
    level = user_level.upper() if isinstance(user_level, str) else ''
    
    # Return the corresponding logging level or fallback to WARNING
    return level_mapping.get(level, logging.WARNING)

# <<< LOGGER <<<

def load_user_module(file_path: str) -> dict[str, SchemeEntry]:
    """Dynamically load a Python module from the given file path."""
    try:
        # Ensure the file path is absolute
        file_path = str(pathlib.Path(file_path).resolve())
        
        # Create a module spec
        spec = importlib.util.spec_from_file_location("user_schemes_module", file_path)
        if spec and spec.loader:
            # Create a new module based on the spec
            user_module = importlib.util.module_from_spec(spec)
            # Execute the module to populate its namespace
            spec.loader.exec_module(user_module)
            
            # Retrieve the user_schemes attribute
            user_schemes = getattr(user_module, "user_schemes", None)
            
            if user_schemes is None or not isinstance(user_schemes, dict):
                raise TypeError(f"'user_schemes' must be a dictionary, got {type(user_schemes)}")
            
            return user_schemes
        else:
            raise ImportError(f"Cannot create a module spec for {file_path}")
    except Exception as e:
        raise ImportError(f"Failed to load user module: {e}")

def trim_str(s:str) -> str:
    """Trim leading and trailing spaces from a string."""
    return s.strip()

def remove_escape_sequences(text:str) -> str:
    # Regular expression to match ANSI escape sequences
    ansi_escape_pattern = r'\x1B\[[0-9;]*[mK]'
    # Replace escape sequences with an empty string
    return re.sub(ansi_escape_pattern, '', text)

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

def run_fzf(fzf_display_options:str,choices: list[str]) -> subprocess.CompletedProcess[str]:
    """Run fzf with the given options."""

    # Split the options into a list
    cmd_user_args: list[str] = shlex.split(fzf_display_options)
    max_h_value = get_max_h_value(cmd_user_args)

    # Compute the required height
    height=len(choices)+4 # number of lines
    if max_h_value:
        height=max(min(height,max_h_value),5)
    
    # Set a list of default argument, which are computed dynamically
    cmd_default_args = ['-h',f'{height:d}']

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

def open_link(editor_open_cmd:str, browser_open_cmd:str, post_handled_link:list[str], opener:OpenerType|str):
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
    if process:
        post_handled_link.insert(0, process)
    
    logger = logging.getLogger()
    logger.debug(post_handled_link)

    try:
        # Run the command and capture stdout and stderr
        proc = subprocess.Popen(
            post_handled_link,
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
        raise CommandFailed(f"failed to execute command '{" ".join(post_handled_link)}': {e}")

def run(
        history_limit:str='',
        editor_open_cmd:str='',
        browser_open_cmd:str='',
        fzf_display_options:str='',
        path_extension:str='',
        loglevel_tmux:str='',
        loglevel_file:str='',
        log_filename:str='',
        user_schemes_path:str=''
    ):

    # Set up the logger
    logger = set_up_logger(loglevel_tmux,loglevel_file,log_filename)

    # Add extra path if provided
    if path_extension and path_extension not in os.environ["PATH"]:
        os.environ["PATH"] = f"{path_extension}:{os.environ['PATH']}"

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

    # Load user schemes
    user_schemes:dict[str, SchemeEntry] = load_user_module(user_schemes_path)

    # Merge both schemes giving precedence to user schemes
    schemes = {**default_schemes, **user_schemes}

    # Find the maximum length in characters of the scheme labels
    max_len_scheme_names:int = max([len(scheme) for scheme in schemes.keys()])

    try:
        # Find pane current path
        current_path = subprocess.check_output(
            ('tmux', 'display', '-p', '#{pane_current_path}',),
            shell=False,
            text=True,
        ).strip()
        # Set current directory to pane current path
        os.chdir(current_path)
    except Exception as e:
        raise FailedChDir(f"current directory could not be changed: {e}")

    # Process each scheme
    for scheme_type,scheme in schemes.items():
        # Use regex.finditer to iterate over all matches
        for match in scheme['regex'].finditer(content):
            entire_match = match.group(0)
            # Extract the match string
            if scheme['pre_handler']:
                pre_handled_text = scheme['pre_handler'](match)
            else:
                pre_handled_text = entire_match 
            # Drop matches for which the pre_handler returns None
            if pre_handled_text and entire_match not in seen:
                seen.add(entire_match)
                # We justify the scheme name for prettier print
                justified_scheme_type=scheme_type.ljust(max_len_scheme_names)
                # We keep a copy of the original matched text for later
                items.append((justified_scheme_type + "  " + pre_handled_text,entire_match,))
    # Clean up no longer needed variables
    del seen

    if items == []:
        logger.info('no link found')
        return

    # Sort items
    sorted_choices = sorted(items, key=lambda x: x[0])

    # Number the items
    numbered_choices = [f"{idx:3d}  {item[0]}" for idx, item in enumerate(sorted_choices, 1)]

    # Run fzf and get selected items
    try:
        # Run fzf and get selected items
        result = run_fzf(fzf_display_options,numbered_choices)
    except FzfError as e:
        logger.error(f"error: unexpected error: {e}")
        sys.exit(1)
    except FzfUserInterrupt as e:
        logger.info("no selection made")
        sys.exit(0)
        
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
                logger.error(f"error: malformed selection: {selected_choice}")
                continue
            
            scheme = schemes.get(scheme_type,None)
            
            if scheme is None:
                logger.error(f"error: malformed selection: {selected_choice}")
                continue

            match=scheme["regex"].search(selected_item)
            if match is None:
                logger.error(f"error: pattern did not match unexpectedly")
                continue          
      
            # Get the post_handler, which applies after the user selection
            post_handler = scheme.get("post_handler",None)

            # Process the match with the post handler
            if post_handler:
                post_handled_link = post_handler(match)    
            else:
                post_handled_link = [match.group(0)]
            
            try:
                open_link(editor_open_cmd,browser_open_cmd,post_handled_link, schemes[scheme_type]["opener"])
            except (NoSuitableAppFound, PatternNotMatching, CommandFailed) as e:
                logger.error(f"error: {e}")
                continue
            except Exception as e:
                logger.error(f"error: unexpected error: {e}")
                continue
        else:
            logger.error(f"error: malformed selection: {selected_choice}")
            continue

if __name__ == "__main__":
    try:
        run(*sys.argv[1:])
    except KeyboardInterrupt:
        logging.info("script interrupted")
    except FailedChDir as e:
        logging.error(f"{e}")
    except Exception as e:
        logging.error(f"unexpected runtime error: {e}")
