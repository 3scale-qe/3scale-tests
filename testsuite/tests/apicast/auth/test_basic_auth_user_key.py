"""
Service requires credentials (app_id, app_key) to be passed using the Basic Auth

Rewrite ./spec/functional_specs/auth/basic_auth_user_key_spec.rb
"""
import pytest

from threescale_api.resources import Service

from testsuite.utils import basic_auth_string


@pytest.fixture(scope="module")
def service_settings(service_settings):
    "Set auth mode to user key"
    service_settings.update(backend_version=Service.AUTH_USER_KEY)
    return service_settings


@pytest.fixture(scope="module")
def service_proxy_settings(service_proxy_settings):
    "Set authorization (Basic HTTP auth) as credentials location"
    service_proxy_settings.update(credentials_location="authorization")
    return service_proxy_settings


@pytest.mark.smoke
def test_should_accept_user_key_passed_by_basic_auth(application, api_client):
    """
    Check credentials passed using the basic auth.
    """
    key = list(application.authobj().credentials.values())[0]

    response = api_client().get('/get')

    assert response.status_code == 200
    assert response.request.headers["Authorization"] == basic_auth_string(key, '')


def test_basic_auth_app_id_403_with_query(application, api_client):
    "Forbid access if credentials passed wrong way"
    client = api_client()

    client.auth = application.authobj(location="headers")

    response = client.get("/get")

    assert response.status_code == 403


def test_basic_auth_app_id_403_without_auth(api_client):
    "Forbid access if no credentials"
    client = api_client()
    client.auth = None
    response = client.get("/get")

    assert response.status_code == 403
