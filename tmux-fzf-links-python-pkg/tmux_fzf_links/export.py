from typing import Callable,TypedDict
import re

from enum import Enum

class OpenerType(Enum):
    EDITOR = 0
    BROWSER = 1
    # when set to custom, the post_handler is responsible to
    # provide the opener as first element of the list
    CUSTOM = 2 

# Define the structure of each scheme entry
class SchemeEntry(TypedDict):
    opener: OpenerType
    pre_handler:Callable[[re.Match[str]], str | None] | None  # A function that takes a string and returns a string
    post_handler: Callable[[re.Match[str]], list[str]] | None  # A function that takes a string and returns a string
    regex: re.Pattern[str]            # A compiled regex pattern

__all__ = ["OpenerType", "SchemeEntry"]
