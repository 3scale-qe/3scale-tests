"""
Tests the cors policy configured to allow multiple origins based on a regex value.
When the "origin" header matches the regex, the "Access-Control-Allow-Origin" header
is set to the value of the "origin" header.
If not, the "Access-Control-Allow-Origin" is not set.
"""

import pytest

from testsuite import rawobj

pytestmark = [
              pytest.mark.require_version("2.10"),
              pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6569"),
             ]


@pytest.fixture(scope="module")
def service(service):
    """
    Set the cors policy to allow requests with "localhost" origin.
    Also sets the headers policy to remove the "Access-Control-Allow-Origin" header from
    the upstream API, so we can test that this header is added by the cors policy.
    """
    proxy = service.proxy.list()
    proxy.policies.insert(0, rawobj.PolicyConfig("cors", {
        "allow_methods": ["GET", "POST"],
        "allow_credentials": True,
        "allow_origin": "(foo|bar).example.com"
        }))
    proxy.policies.insert(0, rawobj.PolicyConfig("headers", {
        "response": [{"op": "delete", "header": "Access-Control-Allow-Origin"}]}))
    return service


def test_cors_headers_for_same_origin(api_client):
    """
    Sends a url in "origin" header matching the regex.
    Asserts that the "Access-Control-Allow-Origin" response header is set to the
    value of the request "origin" header.
    """
    response = api_client().get("/get", headers=dict(origin="foo.example.com"))
    assert response.headers.get("Access-Control-Allow-Origin") == "foo.example.com"


def test_cors_headers_for_disallowed_origin(api_client):
    """
    Sends a url in "origin" header not matching the regex.
    Asserts that the "Access-Control-Allow-Origin" response header is not set by the policy
    """
    response = api_client().get("/get", headers=dict(origin="disallowed.example.com"))
    assert "Access-Control-Allow-Origin" not in response.headers
