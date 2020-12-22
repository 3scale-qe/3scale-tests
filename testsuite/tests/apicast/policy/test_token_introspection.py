"""
Rewriting /spec/functional_specs/policies/token_introspection_spec.rb

When the service is secured by OpenID using RHSSO and the
token introspection policy is set and configured to use rhsso token
introspection endpoint, then a request using rhsso auth passes.
After logging the user out of rhsso, the following requests fail.

"""
import pytest

from testsuite import rawobj
from testsuite.rhsso.rhsso import OIDCClientAuthHook


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(lifecycle_hooks, rhsso_service_info):
    """Have application/service with RHSSO auth configured"""
    lifecycle_hooks.append(OIDCClientAuthHook(rhsso_service_info))


@pytest.fixture(scope="module")
def access_token(application, rhsso_service_info):
    """get RHSSO access token"""
    app_key = application.keys.list()["keys"][0]["key"]["value"]
    return rhsso_service_info.password_authorize(application["client_id"],
                                                 app_key).token['access_token']


@pytest.fixture(scope="module")
def api_client(application):
    """
    Returns api_client without auth session set to None
    Auth session needs to be None when we are testing access_token
    """
    api_client = application.api_client()
    # pylint: disable=protected-access
    api_client._session.auth = None
    return api_client


@pytest.fixture
def update_policies(service, application, rhsso_service_info):
    """
    Adds the token_introspection policy configured as follows
    """

    policy_setting = rawobj.PolicyConfig("token_introspection", {
        "auth-type": "client_id+client_secret",
        "max_ttl_tokens": 10,
        "max_cached_tokens": 10,
        "client_id": application["client_id"],
        "client_secret": application["client_secret"],
        "introspection_url": rhsso_service_info.oidc_client.get_url("token_introspection_endpoint")
    })

    service.proxy.list().policies.append(policy_setting)
    service.proxy.deploy()


# pylint: disable=unused-argument
def test_rhsso_logout(api_client, access_token, rhsso_service_info, update_policies):
    """
    Makes a request using rhsso auth.
    Asserts that the request passed.
    Logs out the user from rhsso.
    Makes another request using rhsso auth.
    Asserts that the request fails
    """

    response = api_client.get("/get", headers={"authorization": "Bearer " + access_token})
    assert response.status_code == 200

    rhsso_service_info.user.logout()

    new_response = api_client.get("/get", headers={"authorization": "Bearer " + access_token})
    assert new_response.status_code == 403
