"""
Rewrite spec/functional_specs/policies/headers/headers_policy_delete_spec.rb
"""

import pytest

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def service(service):
    """Set policy settings"""
    proxy = service.proxy.list()
    proxy.policies.insert(
        0,
        rawobj.PolicyConfig(
            "headers",
            {
                "response": [{"op": "delete", "header": "X-RESPONSE-CUSTOM"}],
                "request": [{"op": "delete", "header": "Accept"}],
            },
        ),
    )
    return service


def test_headers_policy_delete_response(api_client):
    """Test if it delete header from the response"""
    response = api_client().get("/response-headers", params={"X-RESPONSE-CUSTOM": "What ever"})
    assert response.status_code == 200
    assert "X-RESPONSE-CUSTOM" not in response.headers


@pytest.mark.smoke
def test_headers_policy_delete_request(api_client):
    """Test if it delete header from request"""
    response = api_client().get("/get")
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert "Accept" not in echoed_request.headers
