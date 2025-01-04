from pathlib import Path
from .errors_types import LsColorsNotConfigured
import os

# my_module.py
class ColorsSingletonCls:
    _instance = None

    _color_mapping:dict[str,str] = {} # dictionary storing LS_COLORS
    _color_enabled:bool = False # whether to use colors
    tag_color:str = ""  # fallback case
    reset_color:str = ""  # fallback case

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

            # Configure fallback case
            cls._instance.enable_colors(False)
        return cls._instance

    def enable_colors(self,state:bool):
        if state:
            self._color_enabled = True
            self.reset_color = "\033[0m"
            self.tag_color = self.rgb_color(250,130,130)
        else:
            self._color_enabled = False
            self.reset_color = ""
            self.tag_color = ""

    def rgb_color(self,R:int,G:int,B:int):
        if self._color_enabled:
            return f"\033[1;38;2;{R:d};{G:d};{B:d}m"
        else:
            return ""

    def configure_ls_colors_from_str(self,ls_colors:str):
        """Parse the LS_COLORS into a dictionary."""

        for item in ls_colors.split(':'):
            if '=' in item:
                key, value = item.split('=')
                self._color_mapping[key] = value

    def configure_ls_colors_from_file(self,ls_colors_filename:str):
        try:
            with open(ls_colors_filename, 'r') as file:
                ls_colors = file.read().strip()
        except FileNotFoundError:
            raise LsColorsNotConfigured(f"file '{ls_colors_filename}' not found; LS_COLORS cannot be configured")

        self.configure_ls_colors_from_str(ls_colors)
        
    def configure_ls_colors_from_env(self):
        ls_colors = os.getenv('LS_COLORS', None)
        if ls_colors:
            self.configure_ls_colors_from_str(ls_colors)

    def get_file_color(self,filepath: Path) -> str | None:
        """Determine the color for a given file based on LS_COLORS."""
        if not self._color_mapping:
            return None

        # Check for file extension mapping
        ext = filepath.suffix  # Extract the file extension (e.g., '.txt')
        if ext:
            ext_key = f"*{ext}"  # Convert '.txt' to '*.txt'
            if ext_key in self._color_mapping:
                return self._color_mapping[ext_key]

        # Handle specific file types
        if filepath.is_dir():
            return self._color_mapping.get('di', None)  # Directory
        elif filepath.is_symlink():
            return self._color_mapping.get('ln', None)  # Symbolic link
        elif filepath.is_block_device():
            return self._color_mapping.get('bd', None)  # Block device
        elif filepath.is_char_device():
            return self._color_mapping.get('cd', None)  # Character device
        elif filepath.is_fifo():
            return self._color_mapping.get('pi', None)  # Named pipe (FIFO)
        elif filepath.is_socket():
            return self._color_mapping.get('so', None)  # Socket
        elif filepath.is_file() and os.access(filepath, os.X_OK):
            return self._color_mapping.get('ex', None)  # Executable file
        elif filepath.is_file():
            return self._color_mapping.get('fi', None)  # Regular file

        # Handle additional cases based on LS_COLORS
        file_name = filepath.name
        if file_name.startswith('.'):
            return self._color_mapping.get('mh', None)  # Multi-hard link
        elif file_name.endswith('~'):
            return self._color_mapping.get('ow', None)  # Other writable file
        elif not filepath.exists():
            return self._color_mapping.get('mi', None)  # Missing file
        elif filepath.is_symlink() and not filepath.exists():
            return self._color_mapping.get('or', None)  # Orphan symbolic link
        elif filepath.is_symlink() and filepath.is_dir():
            return self._color_mapping.get('tw', None)  # Sticky and other-writable dir

        # Fallback strategy for unknown types
        return self._color_mapping.get('no', None)  # Normal file or fallback

# Instantiate the singleton class
colors = ColorsSingletonCls()

__all__ = ["colors"]