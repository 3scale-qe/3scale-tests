"""
Policy redirecting communication to the Fuse HTTP proxy service when condition is met
in conditional policy condition.

Proxy service is simple camel route, that adds "Fuse-Camel-Proxy" header to the request
"""

import pytest

from packaging.version import Version
from testsuite.echoed_request import EchoedRequest
from testsuite import TESTED_VERSION, rawobj
from testsuite.utils import warn_and_skip

pytestmark = pytest.mark.skipif(TESTED_VERSION < Version("2.16"), reason="TESTED_VERSION < Version('2.16')")


@pytest.fixture(scope="module", autouse=True)
def skip_saas(testconfig):
    """No fuse integration on SaaS"""
    if testconfig["threescale"]["deployment_type"] == "saas":
        warn_and_skip("No fuse integration on SaaS")


@pytest.fixture(scope="module")
def policy_settings(testconfig):
    """Configure API with a http_proxy policy - proxy service is a Camel route deployed in OCP"""

    proxy_service = testconfig["integration"]["service"]["proxy_service"]
    proxy_config = {
        "https_proxy": "https://" + proxy_service,
        "http_proxy": "http://" + proxy_service,
        "all_proxy": "http://" + proxy_service,
    }
    return rawobj.PolicyConfig(
        "conditional",
        {
            "condition": {
                "operations": [
                    {
                        "left": "{{ uri }}",
                        "left_type": "liquid",
                        "op": "==",
                        "right": "/headers/get1",
                        "right_type": "plain",
                    }
                ]
            },
            "policy_chain": [{"name": "http_proxy", "version": "builtin", "configuration": proxy_config}],
        },
    )


@pytest.fixture(scope="module")
def backend_url(private_base_url):
    """Use service URL as backend to avoid hostname conflicts with router.
    Don't use https"""
    return private_base_url("mockserver+svc:1080")


@pytest.fixture(scope="module")
def backends_mapping(backend_url, custom_backend):
    """
    Creates httpbin backend: "/"
    Proxy service used in this test does not support HTTP over TLS (https) protocol,
    therefore http is preferred instead
    """
    return {"/": custom_backend("netty-proxy", backend_url)}


def test_http_proxy_policy(api_client, backend_url):
    """
    Fuse proxy service should add extra Header: "Fuse-Camel-Proxy", when handling communication
    between Apicast and backend API
    """
    response = api_client().get("/headers/get1")
    assert response.status_code == 200
    headers = EchoedRequest.create(response).headers
    assert "Fuse-Camel-Proxy" in headers
    assert headers["Source-Header"] in backend_url

    response = api_client().get("/headers/get2")
    assert response.status_code == 200
    headers = EchoedRequest.create(response).headers
    assert "Fuse-Camel-Proxy" not in headers
    assert "Source-Header" not in headers
