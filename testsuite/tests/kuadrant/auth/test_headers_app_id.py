"""
Service requires credential (app_id) to be passed using headers

"""
import pytest
import utils

# from threescale_api.resources import Service
#
#
# @pytest.fixture(scope="module")
# def service_settings(service_settings):
#     "Set auth mode to app_id/app_key"
#     service_settings.update({"backend_version": Service.AUTH_APP_ID_KEY})
#     return service_settings
#
#
# @pytest.fixture(scope="module")
# def service_proxy_settings(service_proxy_settings):
#     "Set credentials location to 'headers'"
#     service_proxy_settings.update({"credentials_location": "headers"})
#     return service_proxy_settings


@pytest.mark.smoke
def test_auth_headers_app_id(api_client):
    """Test client access using Headers app_id

    Configure Api/Service to use App Id Authentication
    and Headers Auth to pass the credential.

    Then request made with appropriate auth has to pass as expected"""

    auth = utils.UserKeyAuth('ALICE.KEY', 'headers')
    extra_headers = {'Host': 'toystore.127.0.0.1.nip.io'}
    endpoint = 'http://localhost:9080'
    response = api_client(endpoint=endpoint).get('/toy', headers=extra_headers, auth=auth)

    assert response.status_code == 200


def test_basic_auth_app_id_403_with_query(api_client):
    "Forbid access if credentials passed wrong way"

    auth = utils.UserKeyAuth('ALICE.KEY', 'query')
    extra_headers = {'Host': 'toystore.127.0.0.1.nip.io'}
    endpoint = 'http://localhost:9080'
    response = api_client(endpoint=endpoint).get('/toy', headers=extra_headers, auth=auth)

    assert response.status_code == 401


def test_basic_auth_app_id_403_without_auth(api_client):
    "Forbid access if no credentials"
    extra_headers = {'Host': 'toystore.127.0.0.1.nip.io'}
    endpoint = 'http://localhost:9080'
    response = api_client(endpoint=endpoint).get('/toy', headers=extra_headers)

    assert response.status_code == 401
