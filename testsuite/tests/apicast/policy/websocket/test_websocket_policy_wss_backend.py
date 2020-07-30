"""Basic test for websocket policy with wss backend_api"""
from packaging.version import Version  # noqa # pylint: disable=unused-import

import pytest

from websocket import create_connection, WebSocketBadStatusException
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import

# TODO: Remove pylint disable when pytest fixes problem, probably in 6.0.1
# https://github.com/pytest-dev/pytest/pull/7565
# pylint: disable=not-callable
pytestmark = [pytest.mark.skipif("TESTED_VERSION < Version('2.8')"), pytest.mark.flaky]


@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url):
    """Websocket are only available on httpbin go"""
    url = private_base_url("httpbin_go").replace("https://", "wss://", 1)
    return rawobj.Proxy(url)


@pytest.fixture
def user_key(application):
    """User key for application"""
    name = application.service.proxy.list()["auth_user_key"]
    key = application["user_key"]
    return f"?{name}={key}"


def test_basic_websocket_200(websocket_uri, user_key, websocket_options):
    """Basic test for websockets with valid user_key"""
    websocket_uri = websocket_uri + user_key
    websocket = create_connection(websocket_uri, **websocket_options)
    try:
        testing_value = "Websocket testing"
        websocket.send(testing_value)
        response = websocket.recv()
        assert response == testing_value
    finally:
        websocket.close()


def test_basic_websocket_403(websocket_uri, websocket_options):
    """Basic test for websocket with invalid user key"""
    websocket_uri = websocket_uri + "?user_key=123456"
    with pytest.raises(WebSocketBadStatusException, match="Handshake status 403 Forbidden"):
        create_connection(websocket_uri, **websocket_options)


def test_basic_request_200(api_client):
    """Basic test if HTTPS works on product with websocket policy"""
    response = api_client.get("/get")
    assert response.status_code == 200
