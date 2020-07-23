"""Test HTTP_PROXY enviroment variable in Apicast.

Apicast should use all traffic through the defined proxy via HTTP_PROXY env var.
"""
from urllib.parse import urlparse

import pytest

from testsuite import rawobj


pytestmark = pytest.mark.flaky


@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url):
    "Dict of proxy settings to be used when service created"
    return rawobj.Proxy(private_base_url("httpbin_nossl"))


@pytest.fixture(scope="module")
def gateway_environment(gateway_environment, testconfig):
    """Set HTTP_PROXY to staging gateway."""
    proxy_endpoint = testconfig["integration"]["service"]["proxy_service"]

    gateway_environment.update({"HTTP_PROXY": f"http://{proxy_endpoint}"})
    return gateway_environment


def test_proxied_request(api_client, private_base_url):
    """Call to /headers should go through Fuse Camel proxy and return 200 OK."""

    response = api_client.get("/headers")
    assert response.status_code == 200

    headers = response.json()["headers"]

    assert "Fuse-Camel-Proxy" in headers
    assert headers["Source-Header"] == urlparse(private_base_url("httpbin_nossl")).hostname
