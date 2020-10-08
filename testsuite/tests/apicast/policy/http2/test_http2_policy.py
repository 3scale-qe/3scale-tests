"""
Default test for HTTP2 policy
"""
import pytest
import requests

from testsuite import rawobj, HTTP2 # noqa # pylint: disable=unused-import
from testsuite.echoed_request import EchoedRequest
from testsuite.utils import retry_for_session


# CFSSL instance is necessary
pytestmark = [
    pytest.mark.flaky,
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-4684")]


@pytest.fixture(scope="module")
def policy_settings():
    """Http2 policy"""
    return rawobj.PolicyConfig("grpc", {})


@pytest.fixture(scope="module")
def backends_mapping(custom_backend, private_base_url):
    """
    Create backends with paths "/http1" and "/http2"
    """
    return {
        "/http1": custom_backend("http1", private_base_url("httpbin_service")),
        "/http2": custom_backend("http2", private_base_url("httpbin_go_service"))
        }


@pytest.fixture(scope="module")
def api_client(application):
    """Make sure that api_client is using http2"""
    session = requests.session()
    retry_for_session(session)
    session.auth = application.authobj
    return application.api_client(session=session)


def test_full_http2(api_client):
    """
    Test full HTTP2 traffic
    client --> apicast --> backend
    """
    response = api_client.get("/http2/info")
    # client --> apicast
    assert response.status_code == 200
    assert response.raw.version.value == "HTTP/2"

    # apicast --> backend
    echoed_request = EchoedRequest.create(response)
    assert echoed_request.json.get("proto", "") == "HTTP/2.0"


# Skip because the test is using default api_client which is overridden by HTTP2 client
@pytest.mark.skipif("HTTP2")
def test_http1(application):
    """
    Test successful request
    [http1] client --> apicast
    [http2] apicast --> backend
    """
    api_client = application.api_client()

    # client --> apicast
    response = api_client.get("/http2/info")
    assert response.status_code == 200
    assert response.raw.version == 11, "Expected HTTP1.1 version"

    # apicast --> backend
    echoed_request = EchoedRequest.create(response)
    assert echoed_request.json.get("proto", "") == "HTTP/2.0"
