"""
Test headers policy with added backend.
"""
import pytest
from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def backends_mapping(custom_backend, private_base_url):
    """Creates custom backends with paths "/bin", "/lib"""
    return {
        "/bin": custom_backend("backend", private_base_url("httpbin")),
        "/lib": custom_backend("backend2", private_base_url("httpbin")),
    }


@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url):
    """Have httpbin backend due to implementation /response-headers"""
    return rawobj.Proxy(private_base_url("httpbin"))


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


@pytest.mark.parametrize("backend", ["/bin", "/lib"])
def test_headers_policy_doesnt_exist(api_client, backend):
    """will not add header to the response if it does not exist"""
    response = api_client().get(f"{backend}/get")
    echoed_request = EchoedRequest.create(response)

    assert "X-Response-Custom-Add" not in response.headers
    assert "X-Request-Custom-Add" not in echoed_request.headers


@pytest.mark.parametrize("backend", ["/bin", "/lib"])
def test_headers_policy_another_value_to_request(api_client, backend):
    """must add another value to the existing header of the request"""
    response = api_client().get(f"{backend}/get", headers={"X-REQUEST-CUSTOM-ADD": "Original header"})
    echoed_request = EchoedRequest.create(response)

    assert echoed_request.headers["X-Request-Custom-Add"] in (
        "Original header, Additional request header",
        "Original header,Additional request header",
    )


@pytest.mark.parametrize("backend", ["/bin", "/lib"])
def test_headers_policy_another_value_to_response(api_client, backend):
    """must add another value to the existing header of the response"""
    response = api_client().get(f"{backend}/response-headers", params={"X-RESPONSE-CUSTOM-ADD": "Original"})

    assert "X-Response-Custom-Add" in response.headers
    assert response.headers["X-Response-Custom-Add"] == "Original, Additional response header"
