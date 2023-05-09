"""
Tests for the nginx filter policy, that adds the ability to strip a header and not send it to upstream,
or strip the header just for the nginx evaluation, but still send it to the upstream.
"""

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.capabilities import Capability
from testsuite.echoed_request import EchoedRequest

pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.11')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6704"),
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT),
]


@pytest.fixture(scope="module", params=[True, False])
def append_header(request):
    """
    Whether to append the filtered header to upstream or to retain it
    """
    return request.param


@pytest.fixture(scope="module")
def service(service, append_header):
    """
    Configures the nginx header policy to either to strip or retain the "If-Match" header
    based on the append_header fixture
    """
    proxy = service.proxy.list()

    proxy.policies.insert(
        0, rawobj.PolicyConfig("nginx_filters", {"headers": [{"name": "If-Match", "append": append_header}]})
    )
    return service


def test_nginx_filter_if_match(api_client, append_header):
    """
    Asserts that the header is or is not present in the request to upstream
    based on the append_header fixture
    """
    client = api_client()
    response = client.get("/anything", headers={"If-Match": "Anything"})
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert ("If-Match" in echoed_request.headers) == append_header

    if append_header:
        assert echoed_request.headers.get("If-Match") == "Anything"
