# ===============================================================================
#   Author: (c) 2024 Andrea Alberti
# ===============================================================================

from .colors import colors
from .configs import configs
from .hyperlinks import target_for, url_kind
from .opener import OpenerType, PostHandledMatch, PreHandledMatch, SchemeEntry
from .schemes import heuristic_find_file

__all__ = [
    "OpenerType",
    "SchemeEntry",
    "colors",
    "configs",
    "heuristic_find_file",
    "PreHandledMatch",
    "PostHandledMatch",
    "target_for",
    "url_kind",
]
