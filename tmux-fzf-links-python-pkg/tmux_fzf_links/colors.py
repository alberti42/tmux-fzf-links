# colors.py

# ===============================================================================
#   Author: (c) 2024 Andrea Alberti
# ===============================================================================

from __future__ import annotations

import os
from pathlib import Path
from typing import ClassVar

from .errors_types import LsColorsNotConfigured

# Index / tag / dash colors, given as ANSI palette codes (not absolute RGB) so
# the terminal's active theme picks the actual shade and they stay legible when
# switching between light and dark backgrounds. The dash rides the default
# foreground (dim); the index and tag use hues that read on both Latte and
# Frappe. Tags share one uniform color so they read as a calm label column,
# distinct from the per-scheme match hues; the match text carries the type hue.
DEFAULT_TAG_COLOR = 96  # cyan — uniform label color for every tag
DEFAULT_INDEX_COLOR = 94  # bright blue, rendered bold
DEFAULT_DASH_COLOR = 2  # dim default fg


class ColorsSingletonCls:
    _instance: ClassVar[ColorsSingletonCls | None] = None

    _color_mapping: dict[str, str] = {}  # dictionary storing LS_COLORS
    enabled: bool = False  # whether to use colors
    tag_color: str = ""  # fallback case
    index_color: str = ""  # fallback case
    reset_color: str = ""  # fallback case
    dash_color: str = ""  # fallback case
    dim_color: str = ""  # fallback case

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

            # Configure fallback case
            cls._instance.enable_colors(False)
        return cls._instance

    def enable_colors(self, state: bool):
        if state:
            self.enabled = True
            self.reset_color = "\033[0m"
            self.tag_color = self.ansi_color(DEFAULT_TAG_COLOR)
            # bold + hue: blue keeps contrast on light (Latte) and pops on dark (Frappe)
            self.index_color = self.ansi_color(1) + self.ansi_color(DEFAULT_INDEX_COLOR)
            self.dash_color = self.ansi_color(DEFAULT_DASH_COLOR)
            self.dim_color = "\033[2m"
        else:
            self.enabled = False
            self.reset_color = ""
            self.tag_color = ""
            self.index_color = ""
            self.dash_color = ""
            self.dim_color = ""

    def set_tag_color(self, R: int, G: int, B: int) -> None:
        self.tag_color = self.rgb_color(R, G, B)

    def set_index_color(self, R: int, G: int, B: int) -> None:
        self.index_color = self.rgb_color(R, G, B)

    def set_dash_color(self, R: int, G: int, B: int) -> None:
        self.dash_color = self.rgb_color(R, G, B)

    def rgb_color(self, R: int, G: int, B: int):
        if self.enabled:
            return f"\033[38;2;{R:d};{G:d};{B:d}m"
        else:
            return ""

    def ansi_color(self, code: int) -> str:
        """Return an ANSI SGR escape for a color index or attribute.

        Examples: 1 = bold, 2 = dim, 32 = green, 92 = bright green. Bold/dim ride
        the terminal's default foreground (legible on any background); the 30-37 /
        90-97 hues are palette-relative, so the terminal theme picks the shade.
        """
        if self.enabled:
            return f"\033[{code:d}m"
        else:
            return ""

    def configure_ls_colors_from_str(self, ls_colors: str):
        """Parse the LS_COLORS into a dictionary."""

        for item in ls_colors.split(":"):
            if "=" in item:
                key, value = item.split("=")
                self._color_mapping[key] = value

    def configure_ls_colors_from_file(self, ls_colors_filename: str):
        try:
            with open(ls_colors_filename, "r") as file:
                ls_colors = file.read().strip()
        except FileNotFoundError:
            raise LsColorsNotConfigured(
                f"file '{ls_colors_filename}' not found; LS_COLORS cannot be configured"
            )

        self.configure_ls_colors_from_str(ls_colors)

    def configure_ls_colors_from_env(self):
        ls_colors = os.getenv("LS_COLORS", None)
        if ls_colors:
            self.configure_ls_colors_from_str(ls_colors)

    def get_file_color(self, filepath: Path) -> str:
        """Determine the color for a given file based on LS_COLORS.

        Return an empty string as the fallback case when no color code is found for filepath.
        """
        if not self._color_mapping:
            return ""

        # Handle specific file types
        if filepath.is_dir():
            return self._color_mapping.get("di", "")  # Directory
        elif filepath.is_symlink():
            return self._color_mapping.get("ln", "")  # Symbolic link
        elif filepath.is_block_device():
            return self._color_mapping.get("bd", "")  # Block device
        elif filepath.is_char_device():
            return self._color_mapping.get("cd", "")  # Character device
        elif filepath.is_fifo():
            return self._color_mapping.get("pi", "")  # Named pipe (FIFO)
        elif filepath.is_socket():
            return self._color_mapping.get("so", "")  # Socket
        elif filepath.is_file() and os.access(filepath, os.X_OK):
            return self._color_mapping.get("ex", "")  # Executable file

        # Check for file extension mapping
        ext = filepath.suffix  # Extract the file extension (e.g., '.txt')
        if ext:
            ext_key = f"*{ext}"  # Convert '.txt' to '*.txt'
            if ext_key in self._color_mapping:
                return self._color_mapping[ext_key]

        # Handle additional cases based on LS_COLORS
        file_name = filepath.name
        if file_name.startswith("."):
            return self._color_mapping.get("mh", "")  # Multi-hard link
        elif file_name.endswith("~"):
            return self._color_mapping.get("ow", "")  # Other writable file
        elif not filepath.exists():
            return self._color_mapping.get("mi", "")  # Missing file
        elif filepath.is_symlink() and not filepath.exists():
            return self._color_mapping.get("or", "")  # Orphan symbolic link
        elif filepath.is_symlink() and filepath.is_dir():
            return self._color_mapping.get("tw", "")  # Sticky and other-writable dir
        elif filepath.is_file():
            return self._color_mapping.get("fi", "")  # Regular file

        # Fallback strategy for unknown types
        return ""


# Instantiate the singleton class
colors = ColorsSingletonCls()

__all__ = ["colors"]
