import re
from tmux_fzf_links.export import AppType, SchemeEntry

def ip_pre_handler(match:re.Match[str]) -> str | None:
    if not match.group("uri"):
        # keep the match only if no `https?://` precedes the IP address
        return f"{match.group("ip")}"
    else:
        # drop the match
        return None

def ip_post_handler(match:re.Match[str]) -> str:
    return f"https://{match.group(0)}"

# Define schemes
user_schemes: dict[str, SchemeEntry] = {
    "<ip>": {
        "app_type": AppType.BROWSER,
        "post_handler": ip_post_handler,
        "pre_handler": ip_pre_handler,
        "regex": re.compile(r"(?P<uri>https?://)?(?P<ip>[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(\S+))")
        # [0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(:[0-9]{1,5})?(/\S+)*
        },
    }

__all__ = ["user_schemes"]
