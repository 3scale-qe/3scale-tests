"""Basic test for websocket policy with product secured with app id"""
from packaging.version import Version  # noqa # pylint: disable=unused-import

import pytest
from threescale_api.resources import Service

from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.tests.apicast.policy.websocket.conftest import retry_sucessful, retry_failing

pytestmark = [pytest.mark.skipif("TESTED_VERSION < Version('2.8')")]


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


def test_basic_websocket_200(websocket_uri, app_id_app_key, websocket_options):
    """Basic test for websockets with valid app_id and app_key"""
    websocket_uri = websocket_uri + app_id_app_key
    message = "Websocket testing"

    assert message == retry_sucessful(websocket_uri, message, websocket_options)


def test_basic_websocket_403(websocket_uri, application, websocket_options):
    """Basic test for websocket with invalid app_key"""
    app_id = application["application_id"]
    websocket_uri = websocket_uri + f"app_id={app_id}&app_key=invalid"
    expected_message_error = "Handshake status 403 Forbidden"

    assert "403 Forbidden" in retry_failing(websocket_uri, expected_message_error, websocket_options)


def test_basic_request_200(api_client):
    """Basic test if HTTPS works on product with websocket policy"""
    response = api_client.get("/get")
    assert response.status_code == 200
