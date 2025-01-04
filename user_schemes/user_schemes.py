from tmux_fzf_links.export import OpenerType, SchemeEntry, colors
import re

def ip_pre_handler(match:re.Match[str]) -> str | None:
    return match.group("ip")

def ip_post_handler(match:re.Match[str]) -> list[str]:
    ip_addr_str = match.group("ip")
    return [f"https://{ip_addr_str}"]

# Define schemes
user_schemes: list[SchemeEntry] = [
        {   
            "aliases": "IP",
            "opener": OpenerType.BROWSER,
            "post_handler": ip_post_handler,
            "pre_handler": ip_pre_handler,
            "regex": re.compile(r"([\'\" \t\{\[\(\~])(?P<ip>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}[^ \t\)\]\}\"\'\n]+)")
        },
    ]

__all__ = ["user_schemes"]
