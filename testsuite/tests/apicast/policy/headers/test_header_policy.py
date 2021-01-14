"""testing custom headers

Rewrite: ./spec/functional_specs/policies/headers/header_policy_set_spec.rb
"""

import pytest

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def policy_settings():
    """configures headers in policy"""
    return rawobj.PolicyConfig("headers", {
        "response": [{"op": "set",
                      "header": "X-RESPONSE-CUSTOM-SET",
                      "value_type": "plain",
                      "value": "Response set header"}],
        "request": [{"op": "set",
                     "header": "X-REQUEST-CUSTOM-SET",
                     "value_type": "plain",
                     "value": "Request set header"}]})


@pytest.mark.smoke
def test_header_policy(api_client):
    """testing custom header policy"""
    response = api_client().get('/get')
    assert "X-Response-Custom-Set" in response.headers
    assert response.headers["X-Response-Custom-Set"] == "Response set header"

    echoed_request = EchoedRequest.create(response)
    assert "X-Request-Custom-Set" in echoed_request.headers
    assert echoed_request.headers["X-Request-Custom-Set"] == "Request set header"
