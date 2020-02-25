"""
Service requires credentials (app_id, app_key) to be passed using the Basic Auth

Rewrite ./spec/functional_specs/auth/basic_auth_user_key_spec.rb
"""
import base64

import pytest

import threescale_api.auth
from threescale_api.resources import Service


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
def test_should_accept_user_key_passed_by_basic_auth(application, testconfig):
    """
    Check credentials passed using the basic auth.
    """
    key = list(application.authobj.credentials.values())[0]
    encoded_key = base64.b64encode(f"{key}:".encode("utf-8")).decode("utf-8")

    response = application.test_request(verify=testconfig["ssl_verify"])

    assert response.status_code == 200
    assert response.request.headers["Authorization"] == "Basic %s" % encoded_key


def test_basic_auth_app_id_403_with_query(application, testconfig):
    "Forbid access if credentials passed wrong way"
    client = application.api_client(verify=testconfig["ssl_verify"])

    # pylint: disable=protected-access
    client._session.auth = threescale_api.auth.UserKeyAuth(application, "headers")

    response = client.get("/get")

    assert response.status_code == 403


def test_basic_auth_app_id_403_without_auth(application, testconfig):
    "Forbid access if no credentials"
    client = application.api_client(verify=testconfig["ssl_verify"])
    # pylint: disable=protected-access
    client._session.auth = None
    response = client.get("/get")

    assert response.status_code == 403
