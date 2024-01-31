"""
Test if APIAP implicit routing policy has a correct place in the chain.
It should be applied right before APIcast policy.
If it is applied at the start (as was previous behaviour) the upstream policy won't take effect,
because it was already routed.
If it is applied right before APIcast policy, the upstream policy will take an effect
and it will change upstream to echo-api
"""

from urllib.parse import urlparse

import pytest

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def backends_mapping(custom_backend, private_base_url):
    """Create backend mapping to httpbin"""
    return {"/httpbin": custom_backend("backend_two", endpoint=private_base_url("httpbin"))}


@pytest.fixture(scope="module")
def service(service, private_base_url):
    """Add upstream policy"""
    proxy = service.proxy.list()
    proxy.policies.insert(
        0, rawobj.PolicyConfig("upstream", {"rules": [{"url": private_base_url("echo_api"), "regex": "/httpbin"}]})
    )

    return service


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6428")
def test_routing_policy_order(api_client, private_base_url):
    """
    Test if APIAP implicit routing policy has a correct place in the chain.
    """
    client = api_client()

    response = client.get("/httpbin/get")
    assert response.status_code == 200
    echoed_request = EchoedRequest.create(response)
    assert echoed_request.headers["HOST"] == urlparse(private_base_url("echo_api")).hostname
