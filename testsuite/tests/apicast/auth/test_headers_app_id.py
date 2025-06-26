"""
Service requires credential (app_id) to be passed using headers

Rewrite ./spec/functional_specs/auth/headers_app_id_spec.rb
"""

import pytest
from threescale_api.resources import Service


@pytest.fixture(scope="module")
def service_settings(service_settings):
    "Set auth mode to app_id/app_key"
    service_settings.update({"backend_version": Service.AUTH_APP_ID_KEY})
    return service_settings


@pytest.fixture(scope="module")
def service_proxy_settings(service_proxy_settings):
    "Set credentials location to 'headers'"
    service_proxy_settings.update({"credentials_location": "headers"})
    return service_proxy_settings


@pytest.mark.smoke
def test_auth_headers_app_id(application, api_client):
    """Test client access using Headers app_id

    Configure Api/Service to use App Id Authentication
    and Headers Auth to pass the credential.

    Then request made with appropriate auth has to pass as expected"""

    app_id = application.authobj().credentials["app_id"]
    response = api_client().get("/get")

    assert response.status_code == 200
    assert response.request.headers["app_id"] == app_id


def test_basic_auth_app_id_403_with_query(application, api_client):
    "Forbid access if credentials passed wrong way"
    client = api_client()

    # pylint: disable=protected-access
    client.auth = application.authobj(location="query")

    response = client.get("/get")

    assert response.status_code == 403


def test_basic_auth_app_id_403_without_auth(api_client):
    "Forbid access if no credentials"
    client = api_client()
    client.auth = None
    response = client.get("/get")

    assert response.status_code == 403
