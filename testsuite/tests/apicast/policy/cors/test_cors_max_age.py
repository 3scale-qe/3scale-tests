"""
"Add configurable Access-Control-Max-Age header to CORS policy"
"""

import pytest
from testsuite import rawobj


@pytest.fixture(scope="module")
def service(service):
    """
    Set the cors policy to allow requests with "localhost" origin with custom max_age header.
    Also sets the headers policy to remove the "Access-Control-Allow-Origin" header from
    the upstream API, so we can test that this header is not added by the cors policy.
    """
    proxy = service.proxy.list()
    proxy.policies.insert(0, rawobj.PolicyConfig("cors", {
        "allow_methods": ["GET", "POST"],
        "allow_credentials": True,
        "allow_origin": "localhost",
        "max_age": 2500
    }))
    proxy.policies.insert(0, rawobj.PolicyConfig("headers", {
        "response": [{"op": "delete", "header": "Access-Control-Allow-Origin"}]}))
    return service


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6556")
def test_cors_headers_if_contains_custom_max_age(api_client):
    """Request with request with allowed origin that checks for Access-Control-Max-Age"""
    response = api_client().get("/get", headers={"origin": "localhost"})

    assert 'Access-Control-Max-Age' in response.headers
    assert response.headers.get('Access-Control-Max-Age') == "2500"
