"""startup_stall_timeout is hand-editable, so a bad value must not break startup."""

import pytest

from config import STARTUP_STALL_MIN, STARTUP_STALL_TIMEOUT, get_startup_stall_timeout


@pytest.mark.parametrize(
    "cfg, expected",
    [
        ({}, STARTUP_STALL_TIMEOUT),
        ({"startup_stall_timeout": 300}, 300),
        ({"startup_stall_timeout": 0}, 0),  # never give up
        ({"startup_stall_timeout": 450.0}, 450),
        ({"startup_stall_timeout": 5}, STARTUP_STALL_MIN),  # too short
        ({"startup_stall_timeout": -1}, STARTUP_STALL_TIMEOUT),
        ({"startup_stall_timeout": "600"}, STARTUP_STALL_TIMEOUT),
        ({"startup_stall_timeout": None}, STARTUP_STALL_TIMEOUT),
        ({"startup_stall_timeout": True}, STARTUP_STALL_TIMEOUT),
    ],
)
def test_get_startup_stall_timeout(cfg, expected):
    assert get_startup_stall_timeout(cfg) == expected
