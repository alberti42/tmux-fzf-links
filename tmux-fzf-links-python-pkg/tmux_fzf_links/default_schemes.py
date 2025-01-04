import re
import sys
import logging
from os.path import expanduser
from pathlib import Path
from .export import OpenerType, SchemeEntry, get_file_color, rgb_color, reset_color

def git_post_handler(match:re.Match[str]) -> list[str]:
    return [f"https://github.com/{match.group(0)}"]

def error_post_handler(match:re.Match[str]) -> list[str]:
    # Handle error messages appearing on the command line
    # and create an appropriate link to open the affected file 
    
    file=match.group('file')
    line=match.group('line')

    return [f"{file}:{line}"]

def heuristic_find_file(file_path_str:str) -> Path | None:
    # Expand tilde (~) to the user's home directory    
    file_path = Path(expanduser(file_path_str))
    file_path.expanduser
    # Check if the file exists either as is or relative to the current directory
    if file_path.exists():
        return file_path  # Return the absolute path
    else:
        # Drop the match if it corresponds to no file
        return None

def file_pre_handler(match: re.Match[str]) -> str | None:
    # Get the matched file path
    link1 = match.group('link1')
    link2 = match.group('link2')
    
    if link1:
        file_path_str = link1
    else:
        file_path_str = link2


    if file_path_str is None:
        return None

    logging.debug(file_path_str)
    
    # Return the fully resolved path
    resolved_path = heuristic_find_file(file_path_str)
    
    if resolved_path:
        color_code=get_file_color(resolved_path)
        if color_code:
            return f"\033[{color_code}m{str(resolved_path)}\033[0m"
        else:
            return str(resolved_path)
    else:
        return None

def file_post_handler(match:re.Match[str]) -> list[str]:
    file_path_str = match.group(0)
    if sys.platform == "darwin":
        return ['open','-R', str(heuristic_find_file(file_path_str))]
    elif sys.platform == "linux":
        return ['xdg-open', str(heuristic_find_file(file_path_str))]
    elif sys.platform == "win32":
        return ['explorer', str(heuristic_find_file(file_path_str))]
    else:
        raise Exception(f"platform {sys.platform} not supported")

# Define schemes
default_schemes: dict[str, SchemeEntry] = {
    # One can use group names as done in the scheme ERROR to extract subblocks, which are availble to the pre_handler and post_handler
    "[url]": {
        "opener": OpenerType.BROWSER,
        "post_handler": None,
        "pre_handler": lambda m: f"{rgb_color(200,0,255)}{m.group(0)}{reset_color}",
        "regex": re.compile(r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*")
        },
    "[file/dir]": {
        "opener": OpenerType.CUSTOM,
        "post_handler": file_post_handler,
        "pre_handler": file_pre_handler,
        "regex": re.compile(r"(\'(?P<link1>\~?[a-zA-Z0-9_\/\-\:\. ]+)\'|(?P<link2>\~?[a-zA-Z0-9_\/\-\:\.]+))")
        },
    "[git]": {
        "opener":OpenerType.BROWSER,
        "post_handler": git_post_handler,
        "pre_handler": lambda m: f"{rgb_color(0,255,115)}{m.group(0)}{reset_color}",
        "regex": re.compile(r"(ssh://)?git@\S*")
        },
    "[error]": {
        "opener": OpenerType.EDITOR,
        "post_handler": error_post_handler,
        "pre_handler": lambda m: f"{rgb_color(255,0,0)}{m.group("file")}, line {m.group("line")}{reset_color}",
        "regex": re.compile(r"File \"(?P<file>...*?)\"\, line (?P<line>[0-9]+)")
        },
    }

__all__ = ["default_schemes"]
