"""Tests that accessing APIcast with token from a different RHSSO realm does not work
Modified copy of testsuite/tests/apicast/auth/rhsso/openid_rhsso/test_rhsso_wrong_realm.py"""
import pytest

from testsuite.rhsso import Token
from testsuite.utils import blame
from testsuite.capabilities import Capability

pytestmark = pytest.mark.required_capabilities(Capability.SERVICE_MESH)


@pytest.fixture(scope="module")
def user_wrong_realm(rhsso_service_info, request, testconfig):
    """User in a wrong realm"""
    realm = rhsso_service_info.rhsso.create_realm(blame(request, "realm2"), accessTokenLifespan=24 * 60 * 60)

    request.addfinalizer(realm.delete)

    client = realm.create_client(
        name=blame(request, "client2"),
        directAccessGrantsEnabled=True,
        publicClient=False,
        protocol="openid-connect",
        standardFlowEnabled=False)

    username = testconfig["rhsso"]["test_user"]["username"]
    password = testconfig["rhsso"]["test_user"]["password"]
    realm.create_user(username, password)
    return client.oidc_client, username, password


@pytest.fixture(scope="function")
def wrong_realm_token(user_wrong_realm):
    """Token for a wrong realm"""
    client, username, password = user_wrong_realm
    return Token(client.token(username, password))['access_token']


@pytest.fixture(scope="function")
def correct_realm_token(rhsso_service_info, application):
    """Token for a correct realm"""
    return rhsso_service_info.access_token(application)


def test_wrong_realm_auth(api_client, wrong_realm_token, correct_realm_token):
    """Using auth from a different RHSSO realm should fail"""
    client = api_client()
    assert client.get("/get").status_code == 200
    client.auth = None

    response = client.get("/get", headers={"Authorization": f'Bearer {correct_realm_token}'})
    assert response.status_code == 200

    response = client.get("/get")
    assert response.status_code == 403

    response = client.get("/get", headers={"Authorization": f"Bearer {wrong_realm_token}"})
    assert response.status_code == 401
