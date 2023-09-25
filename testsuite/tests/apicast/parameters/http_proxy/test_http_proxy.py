"""Test HTTP_PROXY enviroment variable in Apicast.

Apicast should use all traffic through the defined proxy via HTTP_PROXY env var.
"""

import pytest

from testsuite.echoed_request import EchoedRequest
from testsuite.capabilities import Capability

pytestmark = [pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT)]


@pytest.fixture(scope="module")
def backend_default(private_base_url, custom_backend):
    """
    Default backend with url from private_base_url.
    """
    return custom_backend("backend_default", endpoint=private_base_url("go-httpbin"))


@pytest.fixture(scope="module")
def gateway_environment(gateway_environment, testconfig):
    """Set HTTP_PROXY to staging gateway."""
    proxy_endpoint = testconfig["proxy"]["http"]

    gateway_environment.update({"HTTP_PROXY": proxy_endpoint})
    return gateway_environment


def test_proxied_request(api_client):
    """Call to /headers should go through Fuse Camel proxy and return 200 OK."""

    response = api_client().get("/headers")
    assert response.status_code == 200

    echo = EchoedRequest.create(response)

    assert echo.headers.get("X-Forwarded-By", "MISSING").startswith("MockServer")
