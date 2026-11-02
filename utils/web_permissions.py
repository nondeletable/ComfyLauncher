"""Which web-page permission requests the launcher answers itself.

The embedded browser has no permission prompt, so an unanswered request is
denied — and remembered as denied. ComfyUI nodes that check
``Notification.permission`` (ComfyUI-Custom-Scripts' System Notification) then
show their "notifications are blocked" alert on every node creation. The
launcher only ever shows the local ComfyUI server, so that page is trusted
with notifications; anything else keeps the engine's default.

Shared by both web-view engines, so it stays free of Qt and WebView2 imports.
"""

from __future__ import annotations

from urllib.parse import urlparse

LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def is_local_origin(uri: object) -> bool:
    """True for a URL on this machine (the ComfyUI server we embed)."""
    try:
        return urlparse(str(uri)).hostname in LOCAL_HOSTS
    except ValueError:
        return False


def origin_of(url: str) -> str:
    """``scheme://host[:port]`` of ``url``, the form permission APIs expect."""
    parts = urlparse(url)
    return f"{parts.scheme}://{parts.netloc}"
