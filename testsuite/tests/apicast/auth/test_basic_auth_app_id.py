"""
Service requires credentials (app_id, app_key) to be passed using the Basic Auth
Rewrite ./spec/functional_specs/auth/basic_auth_app_id_spec.rb
"""

import pytest
from threescale_api.resources import Service

from testsuite.httpx import HttpxClient
from testsuite.utils import basic_auth_string


@pytest.fixture(scope="module")
def service_settings(service_settings):
    """Set auth mode to app_id/app_key."""
    service_settings.update(backend_version=Service.AUTH_APP_ID_KEY)
    return service_settings


@pytest.fixture(scope="module")
def service_proxy_settings(service_proxy_settings):
    """Set credentials location to 'authorization' (Basic HTTP auth)."""
    service_proxy_settings.update(credentials_location="authorization")
    return service_proxy_settings


@pytest.fixture(scope="module")
def http_client(application):
    """Provide an HttpxClient instance using HTTP 1.1."""
    client = HttpxClient(False, application)
    client.auth = None  # No default authentication
    yield client
    client.close()


@pytest.fixture(scope="module")
def valid_auth_headers(application):
    """Generate valid Basic Auth headers."""
    creds = application.authobj().credentials
    authorization = basic_auth_string(creds["app_id"], creds["app_key"])
    return {"Authorization": authorization}


@pytest.mark.smoke
def test_basic_auth_success(http_client, valid_auth_headers):
    """Test valid Basic HTTP Auth using app_id and app_key."""
    response = http_client.get("/get", headers=valid_auth_headers)
    assert response.status_code == 200, "Valid request failed unexpectedly."
    assert response.request.headers["Authorization"] == valid_auth_headers["Authorization"]


@pytest.mark.parametrize(
    "auth_method, expected_status",
    [
        ("query", 403),  # Credentials passed as query parameters
        (None, 403),  # No credentials
    ],
)
def test_basic_auth_failure(api_client, application, auth_method, expected_status):
    """Test forbidden access when credentials are passed incorrectly or missing."""
    client = api_client()
    client.auth = application.authobj(location=auth_method) if auth_method else None
    response = client.get("/get")
    assert response.status_code == expected_status
