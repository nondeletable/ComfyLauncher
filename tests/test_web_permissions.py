"""Only the local ComfyUI page is trusted with notifications."""

import pytest

from utils.web_permissions import is_local_origin, origin_of


@pytest.mark.parametrize(
    "uri",
    [
        "http://127.0.0.1:8188",
        "http://127.0.0.1:8188/",
        "http://localhost:8188/some/page",
        "http://[::1]:8188/",
        "https://localhost",
    ],
)
def test_local_server_is_trusted(uri):
    assert is_local_origin(uri)


@pytest.mark.parametrize(
    "uri",
    [
        "https://example.com",
        "http://127.0.0.1.evil.com:8188",
        "http://evil.com/127.0.0.1",
        "http://localhost.evil.com",
        "http://192.168.1.5:8188",
        "",
        "not a url",
        "http://[bad",
    ],
)
def test_everything_else_is_not(uri):
    assert not is_local_origin(uri)


def test_origin_has_no_path():
    assert origin_of("http://127.0.0.1:8188/index.html?x=1") == "http://127.0.0.1:8188"
