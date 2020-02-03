"""Basic test for websocket policy with product secured with app id"""
from packaging.version import Version  # noqa # pylint: disable=unused-import

import pytest
from threescale_api.resources import Service

from websocket import create_connection, WebSocketBadStatusException
from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import

pytestmark = pytest.mark.skipif("TESTED_VERSION < Version('2.8')")


@pytest.fixture
def app_id_app_key(application):
    """App id and app key for an application"""
    app_id = application["application_id"]
    app_key = application.keys.list()["keys"][0]["key"]["value"]
    return f"?app_id={app_id}&app_key={app_key}"


@pytest.fixture(scope="module")
def service_settings(service_settings):
    "Set auth mode to app_id/app_key"
    service_settings.update({"backend_version": Service.AUTH_APP_ID_KEY})
    return service_settings


def test_basic_websocket_200(websocket_uri, app_id_app_key):
    """Basic test for websockets with valid app_id and app_key"""
    websocket_uri = websocket_uri + app_id_app_key
    websocket = create_connection(websocket_uri)
    try:
        testing_value = "Websocket testing"
        websocket.send(testing_value)
        response = websocket.recv()
        assert response == testing_value
    finally:
        websocket.close()


def test_basic_websocket_403(websocket_uri, application):
    """Basic test for websocket with invalid app_key"""
    app_id = application["application_id"]
    websocket_uri = websocket_uri + f"app_id={app_id}&app_key=invalid"
    with pytest.raises(WebSocketBadStatusException, match="Handshake status 403 Forbidden"):
        create_connection(websocket_uri)


def test_basic_request_200(api_client):
    """Basic test if HTTPS works on product with websocket policy"""
    response = api_client.get("/get")
    assert response.status_code == 200
