#!/usr/bin/env python3

#===============================================================================
#   Author: (c) 2024 Andrea Alberti
#===============================================================================

import os
import re
import subprocess
import sys
import logging
import importlib.util
import pathlib

from tmux_fzf_links.fzf_handler import run_fzf
from .colors import colors
from .configs import configs
from typing import override

from .opener import PreHandledMatch, open_link, SchemeEntry
from .errors_types import CommandFailed, FailedChDir, FzfError, FzfUserInterrupt, NoSuitableAppFound, PatternNotMatching, LsColorsNotConfigured
from .default_schemes import default_schemes

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

def load_user_module(file_path: str) -> tuple[list[SchemeEntry],list[str]]:
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

            # Retrieve the rm_default_schemes attribute
            rm_default_schemes = getattr(user_module, "rm_default_schemes", None)
            
            if user_schemes is None or not isinstance(user_schemes, list):
                raise TypeError(f"'user_schemes' must be a list, got {type(user_schemes)}")

            if rm_default_schemes is None:
                rm_default_schemes = []
            if not isinstance(rm_default_schemes, list):
                raise TypeError(f"'rm_default_schemes' must be a list, got {type(rm_default_schemes)}")
            
            return (user_schemes,rm_default_schemes,)
        else:
            raise ImportError(f"cannot create a module spec for {file_path}")
    except Exception as e:
        raise ImportError(f"failed to load user module: {e}")

def trim_str(s:str) -> str:
    """Trim leading and trailing spaces from a string."""
    return s.strip()

def remove_escape_sequences(text:str) -> str:
    # Regular expression to match ANSI escape sequences
    ansi_escape_pattern = r'\x1B\[[0-9;]*[mK]'
    # Replace escape sequences with an empty string
    return re.sub(ansi_escape_pattern, '', text)

def run(
        history_lines:str='',
        editor_open_cmd:str='',
        browser_open_cmd:str='',
        fzf_display_options:str='',
        path_extension:str='',
        loglevel_tmux:str='',
        loglevel_file:str='',
        log_filename:str='',
        user_schemes_path:str='',
        use_ls_colors_str:str='',
        ls_colors_filename:str=''
    ):

    configs.initialize(history_lines,
        editor_open_cmd,
        browser_open_cmd,
        fzf_display_options,
        path_extension,
        loglevel_tmux,
        loglevel_file,
        log_filename,
        user_schemes_path,
        use_ls_colors_str,
        ls_colors_filename)    

    # Set up the logger
    logger = set_up_logger(loglevel_tmux,loglevel_file,log_filename)

    # Add extra path if provided
    if path_extension and path_extension not in os.environ["PATH"]:
        os.environ["PATH"] = f"{path_extension}:{os.environ['PATH']}"

    # Configure LS_COLORS
    if use_ls_colors_str and use_ls_colors_str=='on':
        colors.enable_colors(True)

    if colors.enabled:
        if ls_colors_filename:
            try:
                colors.configure_ls_colors_from_file(ls_colors_filename)
            except LsColorsNotConfigured as e:
                logger.warning(f"{e}")
        else:
            colors.configure_ls_colors_from_env()

    # Capture tmux content
    capture_str:list[str]=['tmux', 'capture-pane', '-J', '-p', '-e', '-S', f'-{history_lines}']
   
    content = subprocess.check_output(
            capture_str,
            shell=False,
            text=True,
        )

    # Remove escape sequences
    content=remove_escape_sequences(content)

    # Load user schemes
    user_schemes:list[SchemeEntry]
    if user_schemes_path:
        loaded_user_module = load_user_module(user_schemes_path)
        user_schemes = loaded_user_module[0]
        rm_default_schemes = loaded_user_module[1]
        # print(rm_default_schemes)
    else:
        user_schemes = []
    
    # Merge both schemes giving precedence to user schemes

    # Set of schemes of already checked out
    schemes:list[SchemeEntry] = []
    checked:set[str] = set()
    for scheme in user_schemes + default_schemes:
        # if none of the tags is already present in 'checked'
        if all(tag not in checked and tag not in rm_default_schemes for tag in scheme["tags"]):
            schemes.append(scheme)
    del checked

    # Create the new dictionary mapping tags to indexes
    tag_to_index = {
        tag: index
        for index, scheme in enumerate(schemes)
        for tag in scheme.get("tags", [])
    }

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

    # We use the unique set as an expedient to sort over
    # pre_handled_text while keeping the original text
    seen:set[str] = set()
    items:list[tuple[PreHandledMatch,str]] = []

    # Process each scheme
    for scheme in schemes:
        # Use regex.finditer to iterate over all matches
        for match in scheme['regex'].finditer(content):
            entire_match = match.group(0)
            # Extract the match string
            pre_handled_match:PreHandledMatch | None
            if scheme['pre_handler']:
                pre_handled_match = scheme['pre_handler'](match)
            else:
                # fallback case when no pre_handler is provided for the scheme
                pre_handled_match = {
                    "display_text": entire_match,
                    "tag": scheme["tags"][0]
                }
            # Drop matches for which the pre_handler returns None
            if pre_handled_match and entire_match not in seen:
                if pre_handled_match["tag"] not in scheme["tags"]:
                    logger.warning(f"the dynamically returned '{pre_handled_match["tag"]}' is not included in: {scheme["tags"]}")
                    continue

                seen.add(entire_match)
                # We keep a copy of the original matched text for later
                items.append((pre_handled_match,entire_match,))
    # Clean up no longer needed variables
    del seen
    
    if items == []:
        logger.info('no link found')
        return

    # Find the maximum length in characters of the display text
    max_len_tag_names:int = max([len(item[0]["tag"]) for item in items])
        
    # Sort items; it is better not to sort the matches alphabetically if we want to preserve
    # the same order of appearance on the screen. For now, this possibility is disabled. We could
    # enable it later by providing an option for the user to decide.
    # sorted_choices = sorted(items, key=lambda x: x[0])
    sorted_choices = items
    sorted_choices.reverse()

    # Number the items
    numbered_choices = [f"{colors.index_color}{idx:4d}{colors.reset_color} {colors.dash_color}-{colors.reset_color} " \
        f"{colors.tag_color}{('['+item[0]["tag"]+']').ljust(max_len_tag_names+2)}{colors.reset_color} {colors.dash_color}-{colors.reset_color} " \
        # add 2 character because of `[` and `]` \
        f"{item[0]["display_text"]}" for idx, item in enumerate(sorted_choices, 1)]

    # Run fzf and get selected items
    try:
        # Run fzf and get selected items
        result = run_fzf(fzf_display_options,numbered_choices,colors.enabled)
    except FzfError as e:
        logger.error(f"error: unexpected error: {e}")
        sys.exit(1)
    except FzfUserInterrupt as e:
        sys.exit(0)    

    # Process selected items
    selected_choices = result.stdout.splitlines()

    # Regular expression to parse the selected item from the fzf options
    # Each line is in the format {four-digit number, two spaces <scheme type>, two spaces, <link>
    selected_item_pattern = r"\s*(?P<idx>\d+)\s*-\s*\[(?P<type>.+?)\]\s*-\s*(?P<link>.+)"

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
            
            index_scheme = tag_to_index.get(scheme_type,None)
            
            if index_scheme is None:
                logger.error(f"error: malformed selection: {selected_choice}")
                continue

            scheme=schemes[index_scheme]

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
                post_handled_link = (match.group(0),)
            
            try:
                open_link(editor_open_cmd,browser_open_cmd,post_handled_link, schemes[index_scheme]["opener"])
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

__all__ = []