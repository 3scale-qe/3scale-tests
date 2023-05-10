"""
Testing that the request/response content limit policy limits the content-length of the
response body
"""
import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import


pytestmark = [
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5244"),
    pytest.mark.skipif("TESTED_VERSION < Version('2.11')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6736"),
]


@pytest.fixture(scope="module")
def policy_settings():
    """
    Enable the content limits policy and sets the request limit
    """
    return rawobj.PolicyConfig("payload_limits", {"response": 100})


@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url):
    """Use httpbin as backend url"""
    return rawobj.Proxy(private_base_url("httpbin"))


@pytest.mark.parametrize("num_bytes,status_code", [(10, 200), (100, 200), (101, 413)])
def test_payload_limits_response(api_client, num_bytes, status_code):
    """
    Tests that the backend response with a content_length greater than the limit
     will produce 413 status code.
    Also asserts that the 'Content-Length' header corresponds to the actual content length.
    - send a request to the httpbin "/bytes/{num_bytes}" endpoint, that will produce a response
      containing a body of length num_bytes
    - if num_bytes < RESPONSE_LIMIT assert 200
    - if num bytes > RESPONSE_LIMIT assert 413
    """
    response = api_client().get(f"/bytes/{num_bytes}")
    assert response.status_code == status_code
    assert response.headers["Content-Length"] == str(len(response.content))
