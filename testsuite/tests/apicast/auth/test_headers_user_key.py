"""
Service requires credentials (user_key) to be passed in headers.

Rewrite: spec/functional_specs/auth/headers_user_key_spec.rb
"""

import pytest
from threescale_api.resources import Service


@pytest.fixture(scope="module")
def service_settings(service_settings):
    "Set auth mode to user key"
    service_settings.update(backend_version=Service.AUTH_USER_KEY)
    return service_settings


@pytest.fixture(scope="module")
def service_proxy_settings(service_proxy_settings):
    "Set headers as credentials location"
    service_proxy_settings.update(credentials_location="headers")
    return service_proxy_settings


def test_headers_user_key(application, api_client):
    """Check credentials passed in headers"""
    key, value = list(application.authobj().credentials.items())[0]
    response = api_client().get("/get")

    assert response.status_code == 200
    assert response.request.headers[key] == value

    client = api_client()
    client.auth = application.authobj(location="query")

    response = client.get("/get")
    assert response.status_code == 403


def test_basic_auth_app_id_403_with_query(application, api_client):
    "Forbid access if credentials passed wrong way"
    client = api_client()

    client.auth = application.authobj(location="authorization")

    response = client.get("/get")

    assert response.status_code == 403


def test_basic_auth_app_id_403_without_auth(api_client):
    "Forbid access if no credentials"
    client = api_client()

    client.auth = None
    response = client.get("/get")

    assert response.status_code == 403
