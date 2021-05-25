"""
"Add configurable Access-Control-Max-Age header to CORS policy"
"""

import pytest
from testsuite import rawobj


@pytest.fixture(scope="module")
def policy_settings():
    """config of cors policy"""

    return rawobj.PolicyConfig("cors", {
        "allow_methods": ["GET", "POST"],
        "allow_credentials": True,
        "allow_origin": "localhost",
        "max_age": 2500
    })


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6556")
def test_cors_headers_if_contains_custom_max_age(api_client):
    """Request with request with allowed origin that checks for Access-Control-Max-Age"""
    response = api_client().get("/get", headers=dict(origin="localhost"))

    assert 'Access-Control-Max-Age' in response.headers
    assert response.headers.get('Access-Control-Max-Age') == "2500"
