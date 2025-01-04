#===============================================================================
#   Author: (c) 2024 Andrea Alberti
#===============================================================================

from os.path import expanduser
from pathlib import Path

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

__all__ = ["heuristic_find_file"]