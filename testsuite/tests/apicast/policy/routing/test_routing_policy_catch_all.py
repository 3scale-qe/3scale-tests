"""
When a routing policy is set with an empty condition, it should be loaded correctly and should route all
the requests to a correct backend.
"""
from urllib.parse import urlparse
import pytest

from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import
from testsuite.echoed_request import EchoedRequest

pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.11')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6415"),
]


@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url):
    """
    Asserts, that echo api is used as the default backend
    """
    return rawobj.Proxy(private_base_url("echo_api"))


@pytest.fixture(scope="module")
def service(service, private_base_url):
    """
    Set the routing policy to route all requests to httpbin.
    (Using the logic that an empty condition should act as a catch all rule)
    """
    proxy = service.proxy.list()
    proxy.policies.insert(
        0,
        rawobj.PolicyConfig(
            "routing",
            {
                "rules": [
                    {
                        "url": private_base_url("httpbin"),
                        "condition": {},
                    }
                ]
            },
        ),
    )

    return service


def test_routing_policy_without_header(api_client, private_base_url):
    """
    Sends a request and asserts, that the routing policy is active and the
    requests is routed to the correct backend (httpbin)
    """
    parsed_url = urlparse(private_base_url("httpbin"))
    response = api_client().get("/get")
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.headers["Host"] == parsed_url.hostname
