"""
Policy redirecting communication to the HTTP proxy service

Proxy service is simple camel route, that adds "Fuse-Camel-Proxy" header to the request
"""

import pytest

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def policy_settings(testconfig):
    """Configure API with a http_proxy policy - proxy service is a Camel route deployed in OCP"""
    proxy_service = testconfig["integration"]["service"]["proxy_service"]
    proxy_config = {
        "https_proxy": "https://" + proxy_service,
        "http_proxy": "http://" + proxy_service,
        "all_proxy": "http://" + proxy_service
    }
    return rawobj.PolicyConfig("http_proxy", proxy_config)


@pytest.fixture(scope="module")
def backends_mapping(private_base_url, custom_backend):
    """
    Creates httpbin backend: "/"
    Proxy service used in this test does not support HTTP over TLS (https) protocol,
    therefore http is preferred instead
    """
    return {"/": custom_backend("netty-proxy", private_base_url("httpbin_service"))}


def test_http_proxy_policy(api_client, private_base_url):
    """
    Fuse proxy service should add extra Header: "Fuse-Camel-Proxy", when handling communication
    between Apicast and backend API
    """
    response = api_client().get("/headers")
    assert response.status_code == 200
    headers = EchoedRequest.create(response).headers
    assert "Fuse-Camel-Proxy" in headers
    assert headers["Source-Header"] in private_base_url("httpbin_service")
