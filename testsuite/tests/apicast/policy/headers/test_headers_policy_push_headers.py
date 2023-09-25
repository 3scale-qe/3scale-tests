"""
Testing proper function of header policy push spec - pushing headers
Rewrite: ./spec/functional_specs/policies/headers/header_policy_push_spec.rb
"""

import pytest

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def backend_default(private_base_url, custom_backend):
    """
    Default backend with url from private_base_url.
    Have httpbin backend due to /response-headers implementation
    """
    return custom_backend("backend_default", endpoint=private_base_url("httpbin"))


@pytest.fixture(scope="module")
def policy_settings():
    "configure headers in policy"
    return rawobj.PolicyConfig(
        "headers",
        {
            "response": [
                {
                    "op": "push",
                    "header": "X-RESPONSE-CUSTOM-PUSH",
                    "value_type": "plain",
                    "value": "Additional response header",
                }
            ],
            "request": [
                {
                    "op": "push",
                    "header": "X-REQUEST-CUSTOM-PUSH",
                    "value_type": "plain",
                    "value": "Additional request header",
                }
            ],
        },
    )


def test_headers_policy_function(api_client):
    """testing custom header policy"""
    response = api_client().get("/get")
    echoed_request = EchoedRequest.create(response)
    assert "X-Response-Custom-Push" in response.headers
    assert echoed_request.headers["X-Request-Custom-Push"] == "Additional request header"


def test_headers_policy_push_header_to_request(api_client):
    """test if is new value pushed to request - existing one"""
    response = api_client().get("/get", headers={"X-Request-Custom-Push": "Original header"})
    echoed_request = EchoedRequest.create(response)

    assert echoed_request.headers["X-Request-Custom-Push"] == "Original header,Additional request header"


def test_headers_policy_push_header_to_response(api_client):
    """test if is new value pushed to response - existing one"""
    response = api_client().get("/response-headers", params={"X-RESPONSE-CUSTOM-PUSH": "Original"})
    assert "X-Response-Custom-Push" in response.headers
    assert response.headers["X-Response-Custom-Push"] == "Original, Additional response header"
