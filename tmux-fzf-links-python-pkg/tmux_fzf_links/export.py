from typing import Callable,TypedDict
import re

from enum import Enum

class AppType(Enum):
    EDITOR = 0
    BROWSER = 1

# Define the structure of each scheme entry
class SchemeEntry(TypedDict):
    app_type:AppType
    pre_handler:Callable[[re.Match[str]], str | None] | None  # A function that takes a string and returns a string
    post_handler: Callable[[re.Match[str]], str] | None  # A function that takes a string and returns a string
    regex: re.Pattern[str]            # A compiled regex pattern

__all__ = ["AppType", "SchemeEntry"]
