#===============================================================================
#   Author: (c) 2024 Andrea Alberti
#===============================================================================

class MissingPostHandler(Exception):
    """Raise exception when the post-handler is missing for a Custom opener type"""

class NotSupportedPlatform(Exception):
    """Raise exception when the current platform is not supported"""

class FailedResolvePath(Exception):
    """Raise exception when resolving path of a file with programming code failed"""

class FailedChDir(Exception):
    """Raise exception when changing directory to tmux pane current directory fails"""

class FailedTmuxPaneSize(Exception):
    """Raise exception when tmux pane height cannot be determined"""

class FailedParsingUserOption(Exception):
    """Raise exception when it fails to parse user options"""

class PatternNotMatching(Exception):
    """Raise exception when the pattern does not match a string already matched"""

class NoSuitableAppFound(Exception):
    """Raise exception when no suitable app was found to open the link"""

class CommandFailed(Exception):
    """Raise exception when the executed app exits with a nonzero return code"""

class NoEditorConfigured(Exception):
    """Raise exception when the file cannot be opened because no editor is configured"""

class NoBrowserConfigured(Exception):
    """Raise exception when the url cannot be opened because no browser is configured"""

class FzfUserInterrupt(Exception):
    """Raise exception when the user cancels fzf modal window"""

class FzfNotFound(Exception):
    """Raise exception when the command fzf is not found in the $PATH"""

class FzfError(Exception):
    """Raise exception when fzf fails"""

class FzfWrongAction(Exception):
    """Raise exception when fzf returns an action that is not supported"""

class LsColorsNotConfigured(Exception):
    """Raise exception when LS_COLORS could not be configured"""

class FileLoggingNotAllow(Exception):
    """Raise exception when logging to file is not allowed"""

__all__ = ["FailedChDir", "FailedTmuxPaneSize", "PatternNotMatching", "NoSuitableAppFound", "CommandFailed", "FzfUserInterrupt", "FzfError", "FailedResolvePath"]