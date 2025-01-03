from .errors_types import LsColorsNotConfigured
import os

_color_mapping:dict[str,str] = {}

def configure_ls_colors(ls_colors_filename:str) -> dict[str,str]:
    """Parse the LS_COLORS environment variable into a dictionary."""
    global _color_mapping

    try:
        with open(ls_colors_filename, 'r') as file:
            ls_colors = file.read().strip()
    except FileNotFoundError:
        raise LsColorsNotConfigured(f"file '{ls_colors_filename}' not found; LS_COLORS cannot be configured")
        
    for item in ls_colors.split(':'):
        if '=' in item:
            key, value = item.split('=')
            _color_mapping[key] = value
    return _color_mapping

def get_file_color(filename:str) -> str | None:
    if not _color_mapping:
        return None

    """Determine the color for a given filename based on LS_COLORS."""
    for key, value in _color_mapping.items():
        if key.startswith('*.') and filename.endswith(key[1:]):
            return value
    # Default colors for directories, executables, etc.
    if os.path.isdir(filename):
        return _color_mapping.get('di', None)
    elif os.access(filename, os.X_OK):
        return _color_mapping.get('ex', None)
    return _color_mapping.get('fi', None)

__all__ = ["get_file_color","configure_ls_colors"]