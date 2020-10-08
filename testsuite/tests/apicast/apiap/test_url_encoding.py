"""
Tests, that when using APIaaP the escaped characters in the request
path are not escaped once again
"""

import pytest

from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def backends_mapping(custom_backend, private_base_url):
    """
    Create backend with a "/foo" path
    """
    return {"/foo": custom_backend("backend_foo", endpoint=private_base_url("echo_api"))}


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5454")
def test_routing_policy_path(api_client):
    """
    Send a request to the /foo/%EF%EF%EF
    The /foo should be removed from the path and the following part should be left
    untouched. In particular, it should not be escaped to "%25EF%25EF%25EF"
    """
    response = api_client.get("/foo/%EF%EF%EF")
    echoed_request = EchoedRequest.create(response)

    assert response.status_code == 200
    assert echoed_request.path == "/%EF%EF%EF"
