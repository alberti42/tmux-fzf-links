# default_schemes.py

#===============================================================================
#   Author: (c) 2024 Andrea Alberti
#===============================================================================

import re
import sys
import shlex
from .export import OpenerType, SchemeEntry, PreHandledMatch, PostHandledMatch, colors, heuristic_find_file, configs
from .errors_types import NotSupportedPlatform, FailedResolvePath

# >>> GIT SCHEME >>>

def git_post_handler(match:re.Match[str]) -> PostHandledMatch:
    server:str = match.group("server")
    repo:str = match.group("repo")
    
    return {'url': f"https://{server}/{repo}"}

git_scheme:SchemeEntry = {
        "tags": ("git",),
        "opener":OpenerType.BROWSER,
        "post_handler": git_post_handler,
        "pre_handler": lambda m: {
            "display_text": f"{colors.rgb_color(0,255,115)}{m.group(0)}{colors.reset_color}",
            "tag": "git"
        },
        "regex": [re.compile(r"(ssh://)?git@(?P<server>[^ \t\n\"\'\)\]\}]+)\:(?P<repo>[^ \.\t\n\"\'\)\]\}]+)")]
    }

# <<< GIT SCHEME <<<

# >>> CODE ERROR SCHEME >>>

def code_error_pre_handler(match: re.Match[str]) -> PreHandledMatch | None:
    file = match.group("file")
    line = match.group("line")

    # fully resolved path
    resolved_path = heuristic_find_file(file)

    if resolved_path is None:
        # drop the match if it cannot resolve the path
        return None

    display_text = f"{colors.rgb_color(255,0,0)}{file}, line {line}{colors.reset_color}"

    suffix = resolved_path.suffix

    if suffix == '.py':
        tag = 'Python'
    else:
        # fallback case
        tag = 'code err.'

    return {"display_text": display_text, "tag": tag}

def code_error_post_handler(match:re.Match[str]) -> PostHandledMatch:
    # Handle error messages appearing on the command line
    # and create an appropriate link to open the affected file 

    file=match.group('file')

    # fully resolved path
    resolved_path = heuristic_find_file(file)

    if resolved_path is None:
        raise FailedResolvePath("could not resolve the path of: {file}")

    line=match.group('line')

    return {'file':str(resolved_path.resolve()), 'line':line}

code_error_scheme:SchemeEntry = {
            "tags": ("code err.","Python"),
            "opener": OpenerType.EDITOR,
            "post_handler": code_error_post_handler,
            "pre_handler": code_error_pre_handler,
            "regex": [re.compile(r"File \"(?P<file>...*?)\"\, line (?P<line>[0-9]+)")]
        }

# <<< CODE ERROR SCHEME <<<

# >>> URL SCHEME >>>

url_scheme:SchemeEntry = {
        "tags": ("url",),
        "opener": OpenerType.BROWSER,
        "post_handler": None,
        "pre_handler": lambda m: {
            "display_text": f"{colors.rgb_color(200,0,255)}{m.group(0)}{colors.reset_color}",
            "tag": "url"
        },
        "regex": [re.compile(r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*")]
    }

# <<< URL SCHEME <<<

# >>> FILE SCHEME >>>

def file_pre_handler(match: re.Match[str]) -> PreHandledMatch | None:
    # Get the matched file path
    file_path:str|None = match.group("link")
    
    if file_path == None:
        # This is not supposed to happen, but to be on the safe side
        return None

    # Drop matches containing only `.` such as current and previous folder
    if all(char == '.' for char in file_path):
        return None
    
    # Drop matches containing only `~` for the home directory
    if file_path == '~':
        return None

    # Return the fully resolved path
    resolved_path = heuristic_find_file(file_path)
    
    if resolved_path == None:
        return None 
    
    tag="dir" if resolved_path.is_dir() else "file"
    if colors.enabled:
        color_code=colors.get_file_color(resolved_path)
        display_text = f"\033[{color_code}m{file_path}\033[0m"
    else:
        display_text = f"{file_path}"
    return { 
        "display_text":display_text,
        "tag": tag
        }

def file_post_handler(match:re.Match[str]) -> PostHandledMatch:

    # Get the matched file path
    file_path:str = match.group("link")
    line:str|None = match.group("line")
    if line is None:
        # Open the first line by default
        line = "1"

    resolved_path = heuristic_find_file(file_path)
    if resolved_path is None:
        raise FailedResolvePath(f"could not resolve the path of: {file_path}")

    resolved_path_str = str(resolved_path)

    if resolved_path.is_file():
        # If file, check whether it is a binary file. Open the file in binary mode and read a portion of it:
        with resolved_path.open('rb') as file:
            chunk = file.read(4096)  # Read the first 1024 bytes
            if b'\0' in chunk:      # Check for null bytes
                is_binary = True
            else:
                is_binary = False

        if not is_binary and configs.editor_open_cmd:
            # If not binary, open the the file with configured editor
            args = shlex.split(configs.editor_open_cmd.replace(f"%file",resolved_path_str).replace(f"%line",line))
            return {'cmd': args[0], 'args':args[1:], 'file': resolved_path_str}
        else:
            configs.logger.warning(f'warning: binary files cannot be opened with the editor: {resolved_path_str}')
            return None
    else:
         # If directory, then cd into the selected directory
        return {'cmd': 'tmux', 'args': ['send-keys', f'cd "{resolved_path_str}"', 'C-m'], 'file':resolved_path_str}
    
file_scheme:SchemeEntry = {
        "tags": ("file","dir",),
        "opener": OpenerType.CUSTOM_OPEN,
        "post_handler": file_post_handler,
        "pre_handler": file_pre_handler,
        "regex": [
            re.compile(r"(?P<link>^[^<>:\"\\|?*\x00-\x1F]+)(\:(?P<line>\d+))?",re.MULTILINE), # filename with spaces, starting at the line beginning
            re.compile(r"\'(?P<link>[^:\'\"|?*\x00-\x1F]+)\'(\:(?P<line>\d+))?"), # filename with spaces, quoted
            re.compile(r"(?P<link>[^\ :\'\"|?*\x00-\x1F]+)(\:(?P<line>\d+))?"), # filename not including spaces
        ]
    }

# <<< FILE SCHEME <<<

# Define schemes
default_schemes: list[SchemeEntry] = [
        url_scheme,
        file_scheme,
        git_scheme,
        code_error_scheme
    ]

__all__ = ["default_schemes"]
