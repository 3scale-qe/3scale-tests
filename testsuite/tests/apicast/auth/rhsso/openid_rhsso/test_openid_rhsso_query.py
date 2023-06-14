"""
Rewrite of the spec/functional_specs/auth/rhsso/openid_rhsso_spec.rb

When the OIDC configuration is used and the credentials location is set to query,
only the calls with correct credentials location will pass.
"""
import pytest

from testsuite.capabilities import Capability
from testsuite.echoed_request import EchoedRequest
from testsuite.rhsso.rhsso import OIDCClientAuthHook

pytestmark = [pytest.mark.issue("https://issues.jboss.org/browse/THREESCALE-1951")]


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(lifecycle_hooks, rhsso_service_info):
    """
    Have application/service with RHSSO auth configured
    Sets the credentials_location to query
    """
    lifecycle_hooks.append(OIDCClientAuthHook(rhsso_service_info, credentials_location="query"))
    return rhsso_service_info


def test_access_token(token):
    """Test checks if the token is not None"""
    assert token is not None


@pytest.mark.parametrize(
    "client_function",
    [
        pytest.param(
            "production_client",
            marks=[pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY), pytest.mark.disruptive],
        ),
        "staging_client",
    ],
)
def test_token_in_query(request, client_function, token):
    """Test checks if the request with access token in query params will succeed on both apicasts."""
    client = request.getfixturevalue(client_function)
    response = client.get("/get", params={"access_token": token})
    assert response.status_code == 200

    echoed_response = EchoedRequest.create(response)
    assert echoed_response.params.get("access_token", "") == token


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5885")
@pytest.mark.xfail
@pytest.mark.parametrize(
    "client_function",
    [
        pytest.param(
            "production_client",
            marks=[pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY), pytest.mark.disruptive],
        ),
        "staging_client",
    ],
)
def test_token_basic_auth(request, client_function, token):
    """Test checks if the request with access token in the basic auth will fail on both apicasts."""
    client = request.getfixturevalue(client_function)
    response = client.get("/get", headers={"authorization": "Bearer " + token})
    assert response.status_code == 403


@pytest.mark.parametrize(
    "client_function",
    [
        pytest.param(
            "production_client",
            marks=[pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY), pytest.mark.disruptive],
        ),
        "staging_client",
    ],
)
def test_token_headers(request, client_function, token):
    """Test checks if the request with access token using headers will fail on both apicasts"""
    client = request.getfixturevalue(client_function)
    response = client.get("/get", headers={"access_token": token})
    assert response.status_code == 403


@pytest.mark.parametrize(
    "client_function",
    [
        pytest.param(
            "production_client",
            marks=[pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY), pytest.mark.disruptive],
        ),
        "staging_client",
    ],
)
def test_invalid_token_in_query(request, client_function):
    """Test checks if the request with invalid access token in query params will fail on both apicasts."""
    client = request.getfixturevalue(client_function)
    response = client.get("/get", params={"access_token": "NotValidAccessToken"})
    assert response.status_code == 403


@pytest.mark.parametrize(
    "client_function",
    [
        pytest.param(
            "production_client",
            marks=[pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY), pytest.mark.disruptive],
        ),
        "staging_client",
    ],
)
def test_client_id_and_secret_in_query(request, client_function, application):
    """Test checks if the request with client id and client secret in the query params will fail on both apicasts"""
    client = request.getfixturevalue(client_function)
    response = client.get(
        "/get", params={"client_id": application["client_id"], "client_secret": application["client_secret"]}
    )
    assert response.status_code == 403
