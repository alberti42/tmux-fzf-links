import re
from tmux_fzf_links.export import AppType, SchemeEntry

# Define schemes
user_schemes: dict[str, SchemeEntry] = {
    "IP": {
        "app_type": AppType.BROWSER,
        "post_handler": None,
        "pre_handler": None, "regex": re.compile(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(:[0-9]{1,5})?(/\S+)*")
        },
    }

__all__ = ["user_schemes"]
