"""Default conftest for statuscode overwrite """
import pytest

from testsuite import rawobj


@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url):
    """Status code overwrite are using httpbin endpoints"""
    return rawobj.Proxy(private_base_url("httpbin"))
