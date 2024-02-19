"""
Conftest for the cors policy
"""

import pytest


@pytest.fixture(scope="module")
def backend_default(private_base_url, custom_backend):
    """
    Default backend with url from private_base_url.
    cors require compatible backend to be used
    """
    return custom_backend("backend_default", endpoint=private_base_url("echo_api"))
