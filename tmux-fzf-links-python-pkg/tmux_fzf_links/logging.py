# logging.py

#===============================================================================
#   Author: (c) 2024 Andrea Alberti
#===============================================================================

import sys
if sys.version_info >= (3, 12):  # For Python 3.12 and newer
    from typing import override
elif sys.version_info < (3, 12):  # For Python 3.8 and older
    # Fallback for Python < 3.12
    def override(method):
        return method

import logging
import subprocess

from .errors_types import FileLoggingNotAllow

class TmuxDisplayHandler(logging.Handler):
    @override
    def emit(self, record:logging.LogRecord):
        # Format the log message
        message = self.format(record)
        try:
            # Determine the display command options based on the log level
            display_options = ["tmux", "display-message"]
            if record.levelno >= logging.WARNING:
                display_options.extend(["-d", "0"])  # Pause the message for warnings and errors

            # Include the message
            display_options.append(message)

            # Use tmux display-message to show the log
            _ = subprocess.run(
                display_options,
                check=True,
                shell=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            # Fallback to console if tmux command fails
            print(f"Failed to display message in tmux: {e}")


def set_up_logger(loglevel_tmux:str,loglevel_file:str,log_filename:str) -> tuple[logging.Logger, TmuxDisplayHandler, logging.FileHandler | None]:

    # Set up the root logger; note: if you decide to create a child logger
    # the root logger level needs to be configured to allow for messages
    # to pass through.
    logger = logging.getLogger()  # root logger when no argument is provided
    # Allow all log messages to pass through; we control the level using handlers
    logger.setLevel(0)

    # Set up tmux log handler
    tmux_handler = setup_tmux_log_handler()
    tmux_handler.setLevel(validate_log_level(loglevel_tmux))
    logger.addHandler(tmux_handler)
    
    file_handler: logging.FileHandler|None = None
    if log_filename:
        # Set up file log handler in a safe way where it checks whether
        # the file is writable; if not, the error is reported over tmux display 
        try:
            file_handler = setup_file_log_handler(log_filename)
            file_handler.setLevel(validate_log_level(loglevel_file))
            logger.addHandler(file_handler)
            init_msg="fzf-links tmux plugin started"
            # Send an initialization message to the file handler only
            file_handler.handle(logging.LogRecord(
                    name=logger.name,
                    level=logging.INFO,
                    pathname=__file__,
                    lineno=0,
                    msg=init_msg,
                    args=None,
                    exc_info=None,
                ))
        except Exception as e:
            # To be safe, remove the handler if it was added
            for handler in logger.handlers:
                if isinstance(handler,logging.FileHandler):
                    logger.removeHandler(handler)
                
            # Set level to zero to make sure that the error is displayed 
            tmux_handler.setLevel(0)
            # Log the error to tmux display and exit 
            raise FileLoggingNotAllow(f"error: logging to file not allowed. Check you have permissions to write to logfile: {log_filename}")

    return (logger, tmux_handler, file_handler,)

def setup_tmux_log_handler() -> TmuxDisplayHandler:

    # === Set up tmux logger ===
    
    # Create and add the TmuxDisplayHandler
    tmux_handler = TmuxDisplayHandler()
    # formatter = logging.Formatter("%(levelname)s: %(message)s")
    formatter = logging.Formatter("fzf-links: %(message)s")
    tmux_handler.setFormatter(formatter)

    return tmux_handler

def setup_file_log_handler(log_filename:str='') -> logging.FileHandler:

    # === Set up file logger ===

    # Configure file log handler and check that the logfile can be written
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    
    return file_handler

def validate_log_level(user_level:str):
    """
    Validates the user-provided log level.
    Falls back to WARNING if the level is invalid.

    Args:
        user_level (str): The log level provided by the user (e.g., 'DEBUG', 'INFO').

    Returns:
        int: A valid logging level.
    """
    # Use the internal mapping of log level names to numeric values
    level_mapping = logging._nameToLevel

    # Convert user input to uppercase for case-insensitive matching
    level = user_level.upper() if isinstance(user_level, str) else ''
    
    # Return the corresponding logging level or fallback to WARNING
    return level_mapping.get(level, logging.WARNING)

__all__ = [ "set_up_logger" ]
