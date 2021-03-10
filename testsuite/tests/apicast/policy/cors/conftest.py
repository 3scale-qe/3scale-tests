"""
Conftest for the cors policy
"""
import pytest
from testsuite import rawobj


@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url):
    """cors require compatible backend to be used"""
    return rawobj.Proxy(private_base_url("echo_api"))
