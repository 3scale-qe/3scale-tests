"""Tests httpbin availability"""

import requests
import pytest


@pytest.mark.parametrize("tool_name", ["httpbin", "httpbin_nossl"])
def test_httpbin(private_base_url, tool_name):
    """
    Sends a get request on a httpbin.
    Asserts that:
        - given tool is running and returns 200
    """
    url = private_base_url(tool_name)
    r = requests.get(url, verify=False)
    assert r.status_code == 200
