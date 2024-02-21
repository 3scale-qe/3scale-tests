"""
Test for https://issues.redhat.com/browse/THREESCALE-10591
"""

import pytest

from testsuite import rawobj
from testsuite.rhsso.rhsso import OIDCClientAuthHook

pytestmark = [pytest.mark.nopersistence]


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(lifecycle_hooks, rhsso_service_info):
    """Have application/service with RHSSO auth configured"""
    lifecycle_hooks.append(OIDCClientAuthHook(rhsso_service_info))

    return rhsso_service_info


@pytest.fixture(scope="module")
def access_token(application, rhsso_service_info):
    """get RHSSO access token"""
    return rhsso_service_info.access_token(application)


@pytest.fixture(scope="module")
def client(api_client):
    """
    Returns api_client without auth session set to None
    Auth session needs to be None when we are testing access_token
    """
    api_client = api_client()

    api_client.auth = None
    return api_client


@pytest.fixture
def update_policies(service):
    """
    Adds the token_introspection policy configured as follows
    """

    policy_setting = rawobj.PolicyConfig(
        "token_introspection",
        {
            "auth_type": "use_3scale_oidc_issuer_endpoint",
            "max_ttl_tokens": 10,
            "max_cached_tokens": 10,
        },
    )

    service.proxy.list().policies.append(policy_setting)
    service.proxy.deploy()


# pylint: disable=unused-argument
@pytest.mark.nopersistence  # Test checks changes during test run hence is incompatible with persistence plugin
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-10591")
def test_rhsso_logout(client, access_token, rhsso_service_info, update_policies):
    """
    Makes a request using rhsso auth.
    Asserts that the request passed.
    Logs out the user from rhsso.
    Makes another request using rhsso auth.
    Asserts that the request fails
    """

    response = client.get("/get", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200

    rhsso_service_info.realm.admin.user_logout(rhsso_service_info.user)

    new_response = client.get("/get", headers={"Authorization": f"Bearer {access_token}"})
    assert new_response.status_code == 403
