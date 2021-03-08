"""
Default test for HTTP2 policy
"""
import pytest

import testsuite
from testsuite import rawobj # noqa # pylint: disable=unused-import
from testsuite.echoed_request import EchoedRequest
from testsuite.capabilities import Capability
from testsuite.httpx import HttpxClient


# CFSSL instance is necessary
pytestmark = [
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY),
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
def http2_client(application):
    """Use Httpx client with http2"""
    client = HttpxClient(True, application)
    client.auth = testsuite.httpx.HttpxUserKeyAuth(application)
    yield client
    client.close()


@pytest.fixture(scope="module")
def http1_client(application):
    """Use Httpx client with http 1.1"""
    client = HttpxClient(False, application)
    client.auth = testsuite.httpx.HttpxUserKeyAuth(application)
    yield client
    client.close()


def test_full_http2(http2_client):
    """
    Test full HTTP2 traffic
    client --> apicast --> backend
    """
    response = http2_client.get("/http2/info")
    # client --> apicast
    assert response.status_code == 200
    assert response.http_version == "HTTP/2"

    # apicast --> backend
    echoed_request = EchoedRequest.create(response)
    assert echoed_request.json.get("proto", "") == "HTTP/2.0"


def test_http1(http1_client):
    """
    Test successful request
    [http1] client --> apicast
    [http2] apicast --> backend
    """

    # client --> apicast
    response = http1_client.get("/http2/info")
    assert response.status_code == 200
    assert response.http_version == "HTTP/1.1", "Expected HTTP1.1 version"

    # apicast --> backend
    echoed_request = EchoedRequest.create(response)
    assert echoed_request.json.get("proto", "") == "HTTP/2.0"
