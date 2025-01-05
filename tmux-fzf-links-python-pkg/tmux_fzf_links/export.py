#===============================================================================
#   Author: (c) 2024 Andrea Alberti
#===============================================================================

from .opener import OpenerType, SchemeEntry, PreHandledMatch
from .schemes import heuristic_find_file
from .colors import colors

__all__ = ["OpenerType", "SchemeEntry", "colors", "heuristic_find_file", "PreHandledMatch"]
