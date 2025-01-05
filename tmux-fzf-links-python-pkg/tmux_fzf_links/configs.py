#===============================================================================
#   Author: (c) 2024 Andrea Alberti
#===============================================================================

class ConfigsCls:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            
        return cls._instance

    def initialize(self,
            history_lines:str,
            editor_open_cmd:str,
            browser_open_cmd:str,
            fzf_display_options:str,
            path_extension:str,
            loglevel_tmux:str,
            loglevel_file:str,
            log_filename:str,
            user_schemes_path:str,
            use_ls_colors_str:str,
            ls_colors_filename:str
        ):      

        self.history_limit = history_lines
        self.editor_open_cmd = editor_open_cmd
        self.browser_open_cmd = browser_open_cmd
        self.fzf_display_options = fzf_display_options
        self.path_extension = path_extension
        self.loglevel_tmux = loglevel_tmux
        self.loglevel_file = loglevel_file
        self.log_filename = log_filename
        self.user_schemes_path = user_schemes_path
        self.use_ls_colors_str = use_ls_colors_str
        self.ls_colors_filename = ls_colors_filename

# Instantiate the singleton class
configs = ConfigsCls()

__all__ = ["configs"]