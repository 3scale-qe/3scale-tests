"""
Rewrite /spec/functional_specs/policies/headers/header_policy_add_spec.rb
"""

import pytest
from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def backend_default(private_base_url, custom_backend):
    """
    Default backend with url from private_base_url.
    Have httpbin backend due to implementation /response-headers
    """
    return custom_backend("backend_default", endpoint=private_base_url("httpbin"))


@pytest.fixture(scope="module")
def policy_settings():
    """configure headers in policy"""
    return rawobj.PolicyConfig(
        "headers",
        {
            "response": [
                {
                    "op": "add",
                    "header": "X-RESPONSE-CUSTOM-ADD",
                    "value_type": "plain",
                    "value": "Additional response header",
                }
            ],
            "request": [
                {
                    "op": "add",
                    "header": "X-REQUEST-CUSTOM-ADD",
                    "value_type": "plain",
                    "value": "Additional request header",
                }
            ],
            "enable": True,
        },
    )


def test_headers_policy_doesnt_exist(api_client):
    """will not add header to the response if it does not exist"""
    response = api_client().get("/get")
    echoed_request = EchoedRequest.create(response)

    assert "X-Response-Custom-Add" not in response.headers
    assert "X-Request-Custom-Add" not in echoed_request.headers


def test_headers_policy_another_value_to_request(api_client):
    """must add another value to the existing header of the request"""
    response = api_client().get("/get", headers={"X-REQUEST-CUSTOM-ADD": "Original header"})
    echoed_request = EchoedRequest.create(response)

    # format can differ based on different backend?
    # proper fix is needed in lib
    assert echoed_request.headers["X-Request-Custom-Add"] in (
        "Original header, Additional request header",
        "Original header,Additional request header",
    )


def test_headers_policy_another_value_to_response(api_client):
    """must add another value to the existing header of the response"""
    response = api_client().get("/response-headers", params={"X-RESPONSE-CUSTOM-ADD": "Original"})

    assert "X-Response-Custom-Add" in response.headers
    assert response.headers["X-Response-Custom-Add"] == "Original, Additional response header"
