"""
Service requires credentials (app_id, app_key) to be passed using the Basic Auth

Rewrite ./spec/functional_specs/auth/basic_auth_app_id_spec.rb
"""
import base64

import pytest

import threescale_api.auth
from threescale_api.resources import Service


@pytest.fixture(scope="module")
def service_settings(service_settings):
    "Set auth mode to app_id/app_key"
    service_settings.update({"backend_version": Service.AUTH_APP_ID_KEY})
    return service_settings


@pytest.fixture(scope="module")
def service_proxy_settings(service_proxy_settings):
    "Set credentials location to 'authorization' (Basic HTTP auth)"
    service_proxy_settings.update({"credentials_location": "authorization"})
    return service_proxy_settings


def test_basic_auth_app_id_key(application, testconfig):
    """Test client access with Basic HTTP Auth using app id and app key

    Configure Api/Service to use App ID / App Key Authentication
    and Basic HTTP Auth to pass the credentials.

    Then request made with appropriate Basic auth made has to pass as expected"""

    creds = application.authobj.credentials
    encoded = base64.b64encode(
        f"{creds['app_id']}:{creds['app_key']}".encode("utf-8")).decode("utf-8")

    response = application.test_request(verify=testconfig["ssl_verify"])

    assert response.status_code == 200
    assert response.request.headers["Authorization"] == "Basic %s" % encoded


def test_basic_auth_app_id_403_with_query(application, testconfig):
    "Forbid access if credentials passed wrong way"
    client = application.api_client(verify=testconfig["ssl_verify"])
    # pylint: disable=W0212  # Yes, I know what I am doing
    client._session.auth = threescale_api.auth.AppIdKeyAuth(application, "query")

    response = client.get("/get")

    assert response.status_code == 403


def test_basic_auth_app_id_403_without_auth(application, testconfig):
    "Forbid access if no credentials"
    client = application.api_client(verify=testconfig["ssl_verify"])
    # pylint: disable=W0212  # Yes, I know what I am doing
    client._session.auth = None

    response = client.get("/get")

    assert response.status_code == 403
