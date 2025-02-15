# configs.py

#===============================================================================
#   Author: (c) 2024 Andrea Alberti
#===============================================================================

import logging

class ConfigurationManager:
    """Parse the configurations and assert their validity"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            
        return cls._instance

    def __init__(self):
        if self._initialized is False:
            self._initialize = True

            self.history_lines:int = 0
            self.editor_open_cmd:str = ""
            self.browser_open_cmd:str = ""
            self.fzf_path:str = "fzf"
            self.fzf_display_options:str = ""
            self.path_extension:str = ""
            self.loglevel_tmux:int = logging.WARNING
            self.loglevel_file:int = logging.DEBUG
            self.log_filename = ""
            self.user_schemes_path = ""
            self.use_ls_colors_str = ""
            self.ls_colors_filename = ""
            self.hide_fzf_header:bool = False

            # Root logger
            self.logger:logging.Logger = logging.getLogger()

    def initialize(self,
            history_lines:str,
            editor_open_cmd:str,
            browser_open_cmd:str,
            fzf_path:str,
            fzf_display_options:str,
            path_extension:str,
            loglevel_tmux:int,
            loglevel_file:int,
            log_filename:str,
            user_schemes_path:str,
            use_ls_colors_str:str,
            ls_colors_filename:str,
            hide_fzf_header:str
        ):

        try:
            self.history_lines = int(history_lines)
        except ValueError as e:
            self.logger.warning(f"Input parameter '@fzf-links-history-lines' must be a positive integer: {e}")
            self.history_lines = 0 # default

        self.editor_open_cmd = editor_open_cmd
        self.browser_open_cmd = browser_open_cmd
        self.fzf_path = fzf_path
        self.fzf_display_options = fzf_display_options
        self.path_extension = path_extension
        self.loglevel_tmux = loglevel_tmux
        self.loglevel_file = loglevel_file
        self.log_filename = log_filename
        self.user_schemes_path = user_schemes_path

        if use_ls_colors_str == 'on':
            self.use_ls_colors_str = True
        elif use_ls_colors_str == 'off':
            self.use_ls_colors_str = False
        else:
            self.logger.warning(f"Input parameter '@fzf-links-use-colors' must either be 'on' or 'off', while it was provided: '{use_ls_colors_str}'")
            self.use_ls_colors_str = False # default
        
        self.ls_colors_filename = ls_colors_filename

        if hide_fzf_header == 'on':
            self.hide_fzf_header = True
        elif hide_fzf_header == 'off':
            self.hide_fzf_header = False
        else:
            self.logger.warning(f"Input parameter '@fzf-links-hide-fzf_header' must either be 'on' or 'off', while it was provided: '{hide_fzf_header}'")
            self.hide_fzf_header = False # default

# Instantiate the singleton class
configs = ConfigurationManager()

__all__ = ["configs"]