#===============================================================================
#   Author: (c) 2024 Andrea Alberti
#===============================================================================

import shutil
import re
import os
import subprocess
from enum import Enum
import sys
from typing import Callable, TypedDict, TypeGuard
if sys.version_info >= (3, 11):  # For Python 3.11 and newer
    from typing import NotRequired
elif sys.version_info < (3, 11):  # For Python 3.10
    pass
import shlex

from .errors_types import CommandFailed, NoBrowserConfigured, NoEditorConfigured, NoSuitableAppFound

class OpenerType(Enum):
    EDITOR = 0
    BROWSER = 1
    # when set to custom, the post_handler is responsible to
    # provide the opener as first element of the list
    CUSTOM = 99  # for backward compatibility; equivalent to CUSTOM_OPEN
    CUSTOM_OPEN = 2
    SYSTEM_OPEN = 3
    REVEAL = 4

class PreHandledMatch(TypedDict):
    display_text: str
    tag: str

if sys.version_info >= (3, 11):
    class PostHandledMatchFileType(TypedDict):
        file: str
        line: NotRequired[str]

    class PostHandledMatchCustomType(TypedDict):
        cmd: str # command to be executed
        args: list[str] # list of arguments provided to the command cmd
        file: NotRequired[str] # if provided, it indicates that a file is associated with the match and can be revealed or opened with system's default file manager
else:
    class PostHandledMatchFileType(TypedDict):
        file: str
        # In Python < 3.11, we can't mark 'line' as NotRequired, so it's omitted
    
    class PostHandledMatchCustomType(TypedDict):
        cmd: str # command to be executed
        args: list[str] # list of arguments provided to the command cmd

class PostHandledMatchUrlType(TypedDict): # keys are optional
    url: str

PostHandledMatchDefinite = PostHandledMatchFileType | PostHandledMatchUrlType | PostHandledMatchCustomType
PostHandledMatch = PostHandledMatchDefinite | None

def isValidPostHandledMatchUrlType(value:PostHandledMatchDefinite) -> TypeGuard[PostHandledMatchUrlType]:
    if 'url' in value:
        return True
    else:
        return False

def isValidPostHandledMatchFileType(value:PostHandledMatchDefinite) -> TypeGuard[PostHandledMatchFileType]:
    if 'file' in value and 'cmd' not in value:
        return True
    else:
        return False

def isValidPostHandledMatchCustomType(value:PostHandledMatchDefinite) -> TypeGuard[PostHandledMatchCustomType]:
    if 'cmd' in value and 'args' in value:
        return True
    else:
        return False

# Pre and post handler types
PreHandler = Callable[[re.Match[str]], PreHandledMatch | None] | None
PostHandler = Callable[[re.Match[str]], PostHandledMatch] | None

# Define the structure of each scheme entry
class SchemeEntry(TypedDict):
    tags: tuple[str,...]
    opener: OpenerType
    pre_handler: PreHandler  # A function that takes a string and returns a string
    post_handler: PostHandler  # A function that takes a string and returns a string
    regex: list[re.Pattern[str]]            # A compiled regex pattern

xdg_open_util: str | None = None
def get_xdg_open_util() -> str | None:
    # Find xdg_open for Linux; if nothing is found, None is returned
    global xdg_open_util
    if xdg_open_util is None:
        xdg_open_util = shutil.which("xdg-open")
    return xdg_open_util

system_open_util: str | None = None
def get_system_open_util() -> str | None:
    global system_open_util
    if system_open_util is None:
        if sys.platform == "darwin":
            cmd = shutil.which("open")
            if cmd:
                system_open_util = f"{cmd} '%file'"
        elif sys.platform == "linux":
            cmd = shutil.which("xdg-open")
            if cmd:
                system_open_util = f"{cmd} '%file'"
        elif sys.platform == "win32":
            cmd = shutil.which("explorer")
            if cmd:
                system_open_util = f"{cmd} '%file'"
        else:
            raise NotSupportedPlatform(f"platform {sys.platform} not supported")
    return system_open_util

reveal_util: str | None = None
def get_reveal_util() -> str | None:
    # Find open for macOS; if nothing is found, None is returned
    global reveal_util
    if reveal_util is None:
        if sys.platform == "darwin":
            cmd = shutil.which("open")
            if cmd:
                reveal_util = f"{cmd} -R '%file'"
        elif sys.platform == "linux":
            cmd = shutil.which("dbus-send")
            if cmd:
                reveal_util = f'{cmd} --session --dest=org.freedesktop.FileManager1 --type=method_call /org/freedesktop/FileManager1 org.freedesktop.FileManager1.ShowItems array:string:"file://%file" string:""'
        elif sys.platform == "win32":
            cmd = shutil.which("explorer")
            if cmd:
                reveal_util = f"{cmd} '%file'"
        else:
            raise NotSupportedPlatform(f"platform {sys.platform} not supported")
    return reveal_util

def cmd_from_template(template:str,post_handled_match:PostHandledMatchUrlType | PostHandledMatchFileType ):
    # The keys in the dictionary represent the placeholders
    # to be replaced in the template with the corresponding values
    cmd_str = template
    for key,value in post_handled_match.items():
        if isinstance(value,str):
            cmd_str = cmd_str.replace(f"%{key}",value)

    return shlex.split(cmd_str)

def spawn_daemon(cmd_plus_args: list[str]):
    """
    - On Unix, uses double-fork daemonization; see double-fork magic, see Stevens' "Advanced Programming in the UNIX Environment" for details (ISBN 0201563177)
    - On Windows, uses DETACHED_PROCESS and CREATE_NEW_PROCESS_GROUP.
    """
    if sys.platform == "win32":
        DETACHED_PROCESS = subprocess.DETACHED_PROCESS
        CREATE_NEW_PROCESS_GROUP = subprocess.CREATE_NEW_PROCESS_GROUP

        try:
            subprocess.Popen(
                cmd_plus_args,
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError as e:
            raise CommandFailed(f"Failed to launch detached process: {e}")
        return

    # UNIX: double-fork for full daemonization
    try:
        pid = os.fork()
        if pid > 0:
            return  # Exit parent
    except OSError as e:
        raise CommandFailed(f"First fork failed: {e}", file=sys.stderr)
        
    os.setsid()  # Create new session

    try:
        pid = os.fork()
        if pid > 0:
            os._exit(0)  # Exit second parent
    except OSError as e:
        raise CommandFailed(f"Second fork failed: {e}", file=sys.stderr)
        
    # Grandchild process — fully detached
    subprocess.Popen(
        cmd_plus_args,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    os._exit(os.EX_OK)

def open_link(post_handled_match:PostHandledMatchDefinite, editor_open_cmd:str, browser_open_cmd:str, opener:OpenerType):
    """Open a link using the appropriate handler."""

    # contains the arguments for subprocess.Popen, including the process to start
    cmd_plus_args:list[str]

    if opener == OpenerType.CUSTOM_OPEN:
        if isValidPostHandledMatchCustomType(post_handled_match):
            cmd_plus_args = [post_handled_match["cmd"]] + post_handled_match["args"]
        else:
            raise RuntimeError("'post_handled_match' is of type 'dict' whereas a type 'list' was expected")
    else:
        # template with the command to be executed
        template:str

        match opener:
            case OpenerType.EDITOR:
                if isValidPostHandledMatchFileType(post_handled_match):
                    if editor_open_cmd:
                        template = editor_open_cmd
                    else:
                        default_editor = os.environ.get('EDITOR',None)
                        default_editor = 'open'
                        if not default_editor:
                            raise NoEditorConfigured("no editor command is configured")
                        template = f"{default_editor} '%file'"
                    cmd_plus_args = cmd_from_template(template,post_handled_match)
                else:
                    raise RuntimeError("'post_handled_match' is not compatible with type: PostHandledMatchFileType")
            case OpenerType.BROWSER:
                if isValidPostHandledMatchUrlType(post_handled_match):
                    if browser_open_cmd:
                        template = browser_open_cmd
                    else:
                        default_browser = os.environ.get('BROWSER',None)
                        if not default_browser:
                            raise NoBrowserConfigured("no browser command is configured")
                        template = f"{default_browser} '%url'"
                    cmd_plus_args = cmd_from_template(template,post_handled_match)
                else:
                    raise RuntimeError("'post_handled_match' is not compatible with type: PostHandledMatchFileType")
            case OpenerType.REVEAL:
                if 'file' in post_handled_match:
                    if (util_cmd := get_reveal_util()):
                        template = util_cmd
                        cmd_plus_args = shlex.split(template.replace(f'%file',post_handled_match['file']))
                else:
                    raise RuntimeError("'post_handled_match' is not compatible with type: PostHandledMatchFileType")
            case OpenerType.SYSTEM_OPEN:
                if 'file' in post_handled_match:
                    if (util_cmd := get_system_open_util()):
                        template = util_cmd
                        cmd_plus_args = shlex.split(template.replace(f'%file',post_handled_match['file']))
                else:
                    raise RuntimeError("'post_handled_match' is not compatible with type: PostHandledMatchFileType")
            case _:
                raise NoSuitableAppFound("no suitable app was found to open the link")

    try:
        spawn_daemon(cmd_plus_args)

    except FileNotFoundError as e:
        raise CommandFailed(f'could not find "{cmd_plus_args[0]}" in the path')

    except Exception as e:
        raise CommandFailed(f'failed to execute command "{" ".join(cmd_plus_args)}"')
