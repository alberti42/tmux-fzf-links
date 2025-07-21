#===============================================================================
#   Author: (c) 2024 Andrea Alberti
#===============================================================================

from os.path import expanduser
from pathlib import Path
import errno

def heuristic_find_file(file_path_str:str) -> Path | None:

    try:            
        # Expand tilde (~) to the user's home directory    
        file_path = Path(expanduser(file_path_str))
        # Check if the file exists either as is or relative to the current directory
        if file_path.exists():
            return file_path.resolve()  # Return the absolute resolved path
        else:
            # Drop the match if it corresponds to no file
            return None
    except OSError as e:
        # Filename too long
        if e.errno == errno.ENAMETOOLONG:
            return None
        else:
            raise e

__all__ = ["heuristic_find_file"]