"""Auth tests for Service Mesh, Service Mesh by default allows both query and headers location at once"""
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


@pytest.mark.parametrize("credentials_location", ["query", "headers"])
def test_request_with_auth(application, credentials_location):
    """Check credentials passed in headers """
    client = application.api_client()

    # pylint: disable=protected-access
    client._session.auth.location = credentials_location
    response = client.get("/get")

    assert response.status_code == 200


def test_request_without_auth(application):
    "Forbid access if no credentials"
    client = application.api_client()
    # pylint: disable=protected-access
    client._session.auth = None
    response = client.get("/get")

    assert response.status_code == 403
