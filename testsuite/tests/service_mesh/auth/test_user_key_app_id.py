"""
Auth tests for user_key and app_id/app_key authentication modes for Service Mesh
Service Mesh by allows both query and headers location to be used
"""
import pytest
from threescale_api.resources import Service

from testsuite.gateways.gateways import Capability

pytestmark = pytest.mark.required_capabilities(Capability.SERVICE_MESH)


@pytest.fixture(scope="module", params=[
    pytest.param(Service.AUTH_USER_KEY, id="user-key"),
    pytest.param(Service.AUTH_APP_ID_KEY, id="app-id")
])
def service_settings(request, service_settings):
    "Set auth mode to user key"
    service_settings.update(backend_version=request.param)
    return service_settings


@pytest.fixture
def invalid_auth(service_settings):
    """Returns different invalid credentials for user_key and app_id/app_key authentication modes"""
    if service_settings["backend_version"] == Service.AUTH_APP_ID_KEY:
        return {"app_id": ":invalid_id", "app_key": ":invalid_key"}
    return {"user_key": "invalid_key"}


# TODO: Remove pylint disable when pytest fixes problem, probably in 6.0.1
# https://github.com/pytest-dev/pytest/pull/7565
# pylint: disable=not-callable
@pytest.mark.parametrize("credentials_location", ["query", "headers"])
def test_request_with_auth(api_client, credentials_location):
    """Check valid credentials passed in query and headers, should return 200"""
    # pylint: disable=protected-access
    api_client._session.auth.location = credentials_location
    response = api_client.get("/get")

    assert response.status_code == 200


# TODO: Remove pylint disable when pytest fixes problem, probably in 6.0.1
# https://github.com/pytest-dev/pytest/pull/7565
# pylint: disable=not-callable
@pytest.mark.parametrize("credentials_location", ["params", "headers"])
def test_request_with_wrong_auth(api_client, invalid_auth, credentials_location):
    """Check wrong credentials passed in query (params) or headers, should fail with 403 """
    # pylint: disable=protected-access
    api_client._session.auth = None

    auth = {credentials_location: invalid_auth}
    response = api_client.get("/get", **auth)

    assert response.status_code == 403


def test_request_without_auth(api_client):
    """Forbid access if no credentials are provided, should fail with 401"""
    # pylint: disable=protected-access
    api_client._session.auth = None
    response = api_client.get("/get")

    assert response.status_code == 401
