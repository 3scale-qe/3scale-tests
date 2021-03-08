"""
Rewrite of the spec/functional_specs/auth/rhsso/openid_rhsso_spec.rb

When the OIDC configuration is used and the credentials location is set to basic auth,
only the calls with correct credentials location will pass.
"""
import pytest
from pytest_cases import parametrize_plus, fixture_ref

from testsuite.echoed_request import EchoedRequest
from testsuite.capabilities import Capability

from testsuite.rhsso.rhsso import OIDCClientAuthHook
from testsuite.tests.apicast.auth.rhsso.openid_rhsso.conftest import production_client, staging_client


# a suspicion that fixture_ref + param-marks doesn't prevent fixture to instantiate
pytestmark = [
    pytest.mark.disruptive,
    pytest.mark.issue("https://issues.jboss.org/browse/THREESCALE-1951")]


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(lifecycle_hooks, rhsso_service_info):
    """
    Have application/service with RHSSO auth configured
    Sets the credentials_location to basic auth
    """
    lifecycle_hooks.append(OIDCClientAuthHook(rhsso_service_info, credentials_location="authorization"))


def test_access_token(token):
    """Test checks if the token is not None"""
    assert token is not None


@parametrize_plus('client', [pytest.param(fixture_ref(production_client), marks=[pytest.mark.required_capabilities(
    Capability.PRODUCTION_GATEWAY), pytest.mark.disruptive]), fixture_ref(staging_client)])
def test_token_basic_auth(client, token):
    """Test checks if the request with access token using basic auth will fail on both apicasts"""
    response = client.get("/get", headers={'authorization': "Bearer " + token})
    assert response.status_code == 200

    echoed_response = EchoedRequest.create(response)
    assert echoed_response.headers.get("Authorization", "") == f"Bearer {token}"


@parametrize_plus('client', [pytest.param(fixture_ref(production_client), marks=[pytest.mark.required_capabilities(
    Capability.PRODUCTION_GATEWAY), pytest.mark.disruptive]), fixture_ref(staging_client)])
def test_token_in_query(client, token):
    """Test checks if the request with access token in query params will succeed on both apicasts."""
    response = client.get("/get", params={'access_token': token})
    assert response.status_code == 403


@parametrize_plus('client', [pytest.param(fixture_ref(production_client), marks=[pytest.mark.required_capabilities(
    Capability.PRODUCTION_GATEWAY), pytest.mark.disruptive]), fixture_ref(staging_client)])
def test_token_headers(client, token):
    """Test checks if the request with access token using basic auth will fail on both apicasts"""
    response = client.get("/get", headers={'access_token': token})
    assert response.status_code == 403


@parametrize_plus('client', [pytest.param(fixture_ref(production_client), marks=[pytest.mark.required_capabilities(
    Capability.PRODUCTION_GATEWAY), pytest.mark.disruptive]), fixture_ref(staging_client)])
def test_invalid_token_basic_auth(client):
    """Test checks if the request with access token using basic auth will fail on both apicasts"""
    response = client.get("/get", headers={'authorization': "Bearer " + "NotValidAccessToken"})
    assert response.status_code == 403


@parametrize_plus('client', [pytest.param(fixture_ref(production_client), marks=[pytest.mark.required_capabilities(
    Capability.PRODUCTION_GATEWAY), pytest.mark.disruptive]), fixture_ref(staging_client)])
def test_client_id_and_secret_in_query(client, application):
    """Test checks if the request with client id and client secret in the query params will fail on both apicasts"""
    response = client.get("/get", params={"client_id": application["client_id"],
                                          "client_secret": application["client_secret"]})
    assert response.status_code == 403
