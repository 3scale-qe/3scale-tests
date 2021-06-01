""""
testing proper function of the CORS policy

Rewrite: ./spec/functional_specs/policies/cors/cors_policy_spec.rb
"""
import pytest
from testsuite import rawobj


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
        "allow_origin": "localhost"}))
    proxy.policies.insert(0, rawobj.PolicyConfig("headers", {
        "response": [{"op": "delete", "header": "Access-Control-Allow-Origin"}]}))
    return service


def test_cors_headers_for_same_origin(api_client):
    """Standard request"""
    response = api_client().get("/get", headers=dict(origin="localhost"))
    assert response.headers.get("Access-Control-Allow-Origin") == "localhost"
    assert response.headers.get("Access-Control-Allow-Credentials") == 'true'
    assert response.headers.get('Access-Control-Max-Age') == "600"
    allow_method = {x.strip() for x in response.headers.get("Access-Control-Allow-Methods").split(",")}
    assert allow_method == {"GET", "POST"}


def test_no_cors_headers_with_none_origin(api_client):
    """
    Access-Control-Allow-Origin is not added to a request without origin header
    """
    response = api_client().get("/get")
    assert "Access-Control-Allow-Origin" not in response.headers


def test_cors_headers_for_different_origin(api_client):
    """
    Access-Control-Allow-Origin is not added to a request with origin header with
    not allowed origin
    """
    response = api_client().get("/get", headers=dict(origin="foo.bar.example.com"))
    assert "Access-Control-Allow-Origin" not in response.headers
