"""
Rewrite of the spec/functional_specs/auth/rhsso/openid_rhsso_spec.rb
JIRA: https://issues.jboss.org/browse/THREESCALE-1951
"""
import pytest
from pytest_cases import parametrize_plus, fixture_ref, fixture_plus

from testsuite.echoed_request import EchoedRequest
from testsuite.gateways.gateways import Capability

pytestmark = [pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY),
              pytest.mark.disruptive]


# Used for parametrize_plus, because normal fixture doesn't work with @parametrize_plus
@fixture_plus(scope="module")
def api_client(api_client):
    """
    Staging client
    The auth of the session is set up to none in order to test different auth methods
    The auth of the request will be passed in test functions
    """
    # pylint: disable=protected-access
    api_client._session.auth = None
    return api_client


# Used for parametrize_plus, because normal fixture doesn't work with @parametrize_plus
@fixture_plus(scope="module")
def prod_client(prod_client):
    """
    Production client
    The auth of the session is set up to none in order to test different auth methods
    The auth of the request will be passed in test functions
    """
    client = prod_client()
    # pylint: disable=protected-access
    client._session.auth = None
    return client


@pytest.fixture
def token(application, rhsso_service_info):
    """Access token for 3scale application that is connected with RHSSO"""
    app_key = application.keys.list()["keys"][0]["key"]["value"]
    return rhsso_service_info.password_authorize(application["client_id"], app_key).token['access_token']


def test_access_token(token):
    """Test checks if the token is not None"""
    assert token is not None


# FIXME: This test is getting 403 status code both on 3.11 and 4.x
# Problem: the credentials location is set to  HTTP basic auth. If we set it to query param this test will pass
# We need to split this test file into 3 separate test files:
# 1 - test that credential location HTTP headers is working and other locations are getting 403 ( possible bugs)
# 2 - test that credentials location query param is working ...
# 3 - test that credentials location HTTP basic auth is working ...
@pytest.mark.flaky
@parametrize_plus('client', [fixture_ref(prod_client), fixture_ref(api_client)])
def test_token_in_query(client, token):
    """Test checks if the request with access token in query params will succeed on both apicasts."""
    response = client.get("/get", params={'access_token': token})
    assert response.status_code == 200

    echoed_response = EchoedRequest(response)
    assert echoed_response.json["args"].get("access_token", "") == token


@parametrize_plus('client', [fixture_ref(prod_client), fixture_ref(api_client)])
def test_token_in_header(client, token):
    """Test checks if the request with access token in headers will succeed on both apicasts."""
    response = client.get("/get", headers={'authorization': "Bearer " + token})
    assert response.status_code == 200

    echoed_response = EchoedRequest(response)
    assert echoed_response.json["headers"].get("Authorization", "") == f"Bearer {token}"


@parametrize_plus('client', [fixture_ref(prod_client), fixture_ref(api_client)])
def test_invalid_token_in_query(client):
    """Test checks if the request with invalid access token in query params will fail on both apicasts."""
    response = client.get("/get", params={'access_token': "NotValidAccessToken"})
    assert response.status_code == 403


@parametrize_plus('client', [fixture_ref(prod_client), fixture_ref(api_client)])
def test_invalid_token_in_header(client):
    """Test checks if the request with invalid access token in headers will fail on both apicasts."""
    response = client.get("/get", headers={'authorization': "Bearer NotValidAccessToken"})
    assert response.status_code == 403


@parametrize_plus('client', [fixture_ref(prod_client), fixture_ref(api_client)])
def test_client_id_and_secret_in_query(client, application):
    """Test checks if the request with client id and client secret in the query params will fail on both apicasts"""
    response = client.get("/get", params={"client_id": application["client_id"],
                                          "client_secret": application["client_secret"]})
    assert response.status_code == 403
