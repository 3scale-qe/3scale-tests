""""testing proper function of the CORS policy

Rewrite: ./spec/functional_specs/policies/cors/cors_policy_spec.rb
"""
import pytest
from testsuite import rawobj


@pytest.fixture(scope="module")
def policy_settings():
    """config of cors policy"""
    return rawobj.PolicyConfig("cors", {
        "allow_methods": ["GET", "POST"],
        "allow_credentials": True,
        "allow_origin": "localhost"})


def test_cors_headers_for_same_origin(api_client):
    """Standard request"""
    response = api_client().get("/get", headers=dict(origin="localhost"))
    assert response.headers.get("Access-Control-Allow-Origin") == "localhost"
    assert response.headers.get("Access-Control-Allow-Credentials") == 'true'
    assert response.headers.get("Access-Control-Allow-Methods") == "GET, POST"


def test_no_cors_headers_with_none_origin(api_client):
    """Request without origin header"""
    response = api_client().get("/get")
    assert "Access-Control-Allow-Origin" not in response.headers


def test_cors_headers_for_different_origin(api_client):
    """Request with different origin"""
    response = api_client().get("/get", headers=dict(origin="foo.bar.example.com"))
    assert "Access-Control-Allow-Origin" in response.headers
