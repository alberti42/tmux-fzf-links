import re
from .export import AppType, SchemeEntry

def git_handler(match:re.Match[str]) -> str:
    return f"https://github.com/{match.group(0)}"

def error_handler(match:re.Match[str]) -> str:
    # Handle error messages appearing on the command line
    # and create an appropriate link to open the affected file 
    
    file=match.group('file')
    line=match.group('line')

    return f"{file}:{line}"

# Define schemes
default_schemes: dict[str, SchemeEntry] = {
    # One can use group names as done in the scheme ERROR to extract subblocks, which are availble to the pre_handler and post_handler
    "URL": {
        "app_type": AppType.BROWSER,
        "post_handler": None,
        "pre_handler": None, "regex": re.compile(r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*")
        },
    "GIT": {
        "app_type":AppType.BROWSER,
        "post_handler": git_handler,
        "pre_handler": None,
        "regex": re.compile(r"(ssh://)?git@\S*")
        },
    "ERROR": {
        "app_type": AppType.EDITOR,
        "post_handler": error_handler,
        "pre_handler": None, "regex": re.compile(r"File \"(?P<file>...*?)\"\, line (?P<line>[0-9]+)")
        }
    }

__all__ = ["default_schemes"]
