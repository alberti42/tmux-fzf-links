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
import unicodedata

from tmux_fzf_links.fzf_handler import FzfReturnType, run_fzf
from tmux_fzf_links.logging import set_up_logger
from typing import Generator, Match
from .colors import colors
from .configs import configs

if sys.version_info >= (3, 12):  # For Python 3.12 and newer
    from typing import override
elif sys.version_info < (3, 12):  # For Python 3.8 and older
    # Fallback for Python < 3.12
    def override(method):
        return method
        
from .opener import OpenerType, PreHandledMatch, PostHandledMatch, open_link, SchemeEntry
from .errors_types import FailedTmuxPaneSize, CommandFailed, FailedChDir, FileLoggingNotAllow, FzfError, FzfNotFound, FzfUserInterrupt, MissingPostHandler, NoBrowserConfigured, NoEditorConfigured, NoSuitableAppFound, PatternNotMatching, LsColorsNotConfigured
from .default_schemes import default_schemes

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

def run(
        history_lines:str,
        editor_open_cmd:str,
        browser_open_cmd:str,
        fzf_path:str,
        fzf_display_options:str,
        path_extension:str,
        loglevel_tmux:str,
        loglevel_file:str,
        log_filename:str,
        user_schemes_path:str,
        use_ls_colors_str:str,
        ls_colors_filename:str,
        hide_fzf_header:str,
    ):

    # First thing: set up the logger
    logger, tmux_log_handler, file_log_handler = set_up_logger(loglevel_tmux,loglevel_file,log_filename)

    configs.initialize(history_lines,
        editor_open_cmd,
        browser_open_cmd,
        fzf_path,
        fzf_display_options,
        path_extension,
        tmux_log_handler.level,
        file_log_handler.level if file_log_handler else 0, # pass 0 if file logging is not needed
        log_filename,
        user_schemes_path,
        use_ls_colors_str,
        ls_colors_filename,
        hide_fzf_header)    

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

    # Retrieve the current pane size
    try:
        pane_size_str:str = subprocess.check_output(
            ('tmux', 'display', '-p', '#{pane_height},#{pane_width},#{scroll_position},',),
            shell=False,
            text=True,
        )
        pane_size_list = pane_size_str.split(',')
        pane_height = int(pane_size_list[0])
        pane_width = int(pane_size_list[1])

        scroll_position:int
        if pane_size_list[2]:
            scroll_position = int(pane_size_list[2])
        else:
            scroll_position = 0
        
    except Exception as e:
        raise FailedTmuxPaneSize(f"tmux pane size could not be determined: {e}")

    # Capture tmux content
    capture_str:list[str]=[
        'tmux', 'capture-pane',
        '-J',
        '-p',
        '-S', f'{-scroll_position-configs.history_lines}',
        '-E', f'{pane_height-scroll_position-1}']

    content = subprocess.check_output(
            capture_str,
            shell=False,
            text=True,
        )

    # To deal with two different forms of handling diactrics, we normalize the string
    content = unicodedata.normalize("NFC", content)
    
    # Load user schemes
    user_schemes:list[SchemeEntry]
    rm_default_schemes:list[str]
    if user_schemes_path:
        loaded_user_module = load_user_module(user_schemes_path)
        user_schemes = loaded_user_module[0]
        for user_scheme in user_schemes:
            # Translation for backward compatibility
            if user_scheme["opener"] == OpenerType.CUSTOM:
                user_scheme["opener"] = OpenerType.CUSTOM_OPEN
        rm_default_schemes = loaded_user_module[1]
        # print(rm_default_schemes)
    else:
        user_schemes = []
        rm_default_schemes = []
    
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
    items:list[tuple[PreHandledMatch,str,int,Match[str]]] = []

    # Process each scheme
    for scheme in schemes:
        # Use regex.finditer to iterate over all matches
        for regex in scheme["regex"]:
            for match in regex.finditer(content):
            
                entire_match:str = match.group(0)
                match_start:int = match.start()
                
                # Extract and process the matching string
                pre_handled_match:PreHandledMatch | None
                if scheme["pre_handler"]:
                    pre_handled_match = scheme["pre_handler"](match)
                else:
                    # fallback case when no pre_handler is provided for the scheme
                    pre_handled_match = {
                        "display_text": entire_match,
                        "tag": scheme["tags"][0]
                    }

                # Validate the current match
                if pre_handled_match:
                    
                    # Skip matches for which the pre_handler returns None
                    # Skip matches for texts that has already been processed by a previous scheme
                    if entire_match not in seen:
                        if pre_handled_match["tag"] not in scheme["tags"]:
                            logger.warning(f"the tag returned dynamically '{pre_handled_match['tag']}' is not included in: {scheme['tags']}")
                            continue

                        seen.add(entire_match)
                        # We keep a copy of the original matched text for later
                        items.append((pre_handled_match,entire_match,match_start,match,))
    # Clean up no longer needed variables
    del seen
    
    if items == []:
        logger.info('no link found')
        return

    # Sort items
    items.sort(key=lambda x: x[2],reverse=True)

    # Find the maximum length in characters of the display text
    max_len_tag_names:int = max([len(item[0]["tag"]) for item in items])
        
    # Number the items
    numbered_choices = [f"{colors.index_color}{idx:4d}{colors.reset_color} {colors.dash_color}-{colors.reset_color} " \
        f"{colors.tag_color}{('['+item[0]['tag']+']').ljust(max_len_tag_names+2)}{colors.reset_color} {colors.dash_color}-{colors.reset_color} " \
        # add 2 character because of `[` and `]` \
        f"{item[0]['display_text']}" for idx, item in enumerate(items, 1)]

    # Run fzf and get selected items
    try:
        # Run fzf and get selected items
        fzf_result:FzfReturnType = run_fzf(configs.fzf_path,configs.fzf_display_options,numbered_choices,colors.enabled,pane_height,pane_width)
    except FzfUserInterrupt as e:
        sys.exit(0)

    # Disable colors; this is relevant when producing the pre_handled_match
    colors.enable_colors(False)

    # Regular expression to parse the selected item from the fzf options
    # Each line is in the format {four-digit number, two spaces <scheme type>, two spaces, <link>
    selected_item_pattern = r"\s*(?P<idx>\d+)\s*-\s*\[(?P<type>.+?)\]\s*-\s*(?P<link>.+)"

    # Array of strings to be copied to clipboard
    clipboard:list[str] = []
    
    # Process selected items
    for selected_choice in fzf_result["selection"]:
        fzf_match = re.match(selected_item_pattern, selected_choice)
        if fzf_match:
            idx_str:str = fzf_match.group("idx")
            scheme_type:str = fzf_match.group("type")
            # displayed text created by the prehandler
            pre_handled_match_text:str = fzf_match.group("link")
            
            try:
                idx:int=int(idx_str,10)
                # pick the original item to be searched again
                # before passing the `fzf_match` object to the post handler
                selected_item=items[idx-1]
            except:
                logger.error(f"error: malformed selection: {selected_choice}")
                continue
            
            index_scheme = tag_to_index.get(scheme_type,None)
            
            if index_scheme is None:
                logger.error(f"error: malformed selection: {selected_choice}")
                continue

            scheme=schemes[index_scheme]

            selected_match=selected_item[3]

            if fzf_result["action"] == "COPY_TO_CLIPBOARD":
                # Copy to clipboard the result of the pre handler.
                clipboard.append(pre_handled_match_text)
                # Skip the rest
                continue
                
            # Get the post_handler, which applies after the user selection
            post_handler = scheme.get("post_handler",None)
            
            # Process the rematch with the post handler
            post_handled_link: PostHandledMatch
            if post_handler:
                post_handled_link = post_handler(selected_match)
                if post_handled_link is None:
                    continue
            else:
                if scheme["opener"] == OpenerType.EDITOR:
                    post_handled_link = {'file':selected_match.group(0)}
                elif scheme["opener"] == OpenerType.BROWSER:
                    post_handled_link = {'url':selected_match.group(0)}
                else:
                    raise MissingPostHandler(f"scheme with tags {scheme['tags']} configured as custom opener but missing post handler")
            
            match fzf_result["action"]:
                case "REVEAL":
                    if "file" in post_handled_link:
                        # When the match yields file
                        scheme["opener"] = OpenerType.REVEAL;
                        post_handled_link = {'file': post_handled_link['file']}
                    else:
                        # Display warning and the skip this selected item
                        logger.warning(f'warning: cannot reveal selected choice in system file manager: {selected_match.group(0)}')
                        continue                        
                case "SYSTEM_OPEN":
                    if "file" in post_handled_link:
                        # When the match yields file
                        scheme["opener"] = OpenerType.SYSTEM_OPEN;
                        post_handled_link = {'file': post_handled_link['file']}
                    else:
                        # Display warning and the skip this selected item
                        logger.warning(f'warning: cannot open selected choice with system\'s default opener: {selected_match.group(0)}')
                        continue                        
            
            try:
                open_link(post_handled_link,editor_open_cmd,browser_open_cmd,schemes[index_scheme]["opener"])
            except (NoSuitableAppFound, PatternNotMatching, CommandFailed, NoEditorConfigured, NoBrowserConfigured) as e:
                logger.error(f"error: {e}")
                continue
            except Exception as e:
                logger.error(f"error: unexpected error: {e}")
                continue
        else:
            logger.error(f"error: malformed selection: {selected_choice}")
            continue

    if clipboard != []:    
        plural:str = "s" if len(clipboard)>1 else ""
        clipped_text = "\n".join(clipboard)
        tmux_buffer_action:PostHandledMatch = {
            'cmd': 'tmux',
            'args': ['set-buffer', '-w', f'{clipped_text}', ';', 'display-message', f"copied selection{plural} to tmux buffer"]
        }
        try:
            open_link(tmux_buffer_action,editor_open_cmd,browser_open_cmd,OpenerType.CUSTOM_OPEN)
        except (NoSuitableAppFound, PatternNotMatching, CommandFailed) as e:
            logger.error(f"error: {e}")
            return
        except Exception as e:
            logger.error(f"error: unexpected error: {e}")
            return

if __name__ == "__main__":
    try:
        run(*sys.argv[1:])
    except KeyboardInterrupt:
        logging.info("script interrupted")
    except (FzfError,FzfNotFound,FileLoggingNotAllow,FailedChDir,MissingPostHandler,) as e:
        logging.error(f"{e}")
    except Exception as e:
        logging.error(f"unexpected runtime error: {e}")

__all__ = []
