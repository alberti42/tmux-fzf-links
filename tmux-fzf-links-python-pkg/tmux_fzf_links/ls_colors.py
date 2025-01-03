from pathlib import Path
from .errors_types import LsColorsNotConfigured
import os

_color_mapping:dict[str,str] = {}

def _parse_ls_colors(ls_colors:str) -> dict[str,str]:
    for item in ls_colors.split(':'):
        if '=' in item:
            key, value = item.split('=')
            _color_mapping[key] = value
    return _color_mapping

def configure_ls_colors_from_file(ls_colors_filename:str) -> dict[str,str]:
    """Parse the LS_COLORS environment variable into a dictionary."""
    global _color_mapping

    try:
        with open(ls_colors_filename, 'r') as file:
            ls_colors = file.read().strip()
    except FileNotFoundError:
        raise LsColorsNotConfigured(f"file '{ls_colors_filename}' not found; LS_COLORS cannot be configured")
        
    return _parse_ls_colors(ls_colors)

def configure_ls_colors_from_env() -> dict[str,str]:

    ls_colors = os.getenv('LS_COLORS', None)
    
    if ls_colors:
        return _parse_ls_colors(ls_colors)
    else:
        return {}

def get_file_color(filepath: Path) -> str | None:
    """Determine the color for a given file based on LS_COLORS."""
    if not _color_mapping:
        return None

    # Check for file extension mapping
    ext = filepath.suffix  # Extract the file extension (e.g., '.txt')
    if ext:
        ext_key = f"*{ext}"  # Convert '.txt' to '*.txt'
        if ext_key in _color_mapping:
            return _color_mapping[ext_key]

    # Handle specific file types
    if filepath.is_dir():
        return _color_mapping.get('di', None)  # Directory
    elif filepath.is_symlink():
        return _color_mapping.get('ln', None)  # Symbolic link
    elif filepath.is_block_device():
        return _color_mapping.get('bd', None)  # Block device
    elif filepath.is_char_device():
        return _color_mapping.get('cd', None)  # Character device
    elif filepath.is_fifo():
        return _color_mapping.get('pi', None)  # Named pipe (FIFO)
    elif filepath.is_socket():
        return _color_mapping.get('so', None)  # Socket
    elif filepath.is_file() and os.access(filepath, os.X_OK):
        return _color_mapping.get('ex', None)  # Executable file
    elif filepath.is_file():
        return _color_mapping.get('fi', None)  # Regular file

    # Handle additional cases based on LS_COLORS
    file_name = filepath.name
    if file_name.startswith('.'):
        return _color_mapping.get('mh', None)  # Multi-hard link
    elif file_name.endswith('~'):
        return _color_mapping.get('ow', None)  # Other writable file
    elif not filepath.exists():
        return _color_mapping.get('mi', None)  # Missing file
    elif filepath.is_symlink() and not filepath.exists():
        return _color_mapping.get('or', None)  # Orphan symbolic link
    elif filepath.is_symlink() and filepath.is_dir():
        return _color_mapping.get('tw', None)  # Sticky and other-writable dir

    # Fallback strategy for unknown types
    return _color_mapping.get('no', None)  # Normal file or fallback


__all__ = ["get_file_color","configure_ls_colors_from_env","configure_ls_colors_from_file"]