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
    
class LsColorsNotConfigured(Exception):
    """Raise exception when LS_COLORS could not be configured"""

__all__ = ["FailedChDir", "FailedTmuxPaneHeight", "PatternNotMatching", "NoSuitableAppFound", "CommandFailed", "FzfUserInterrupt", "FzfError", "FailedResolvePath"]