"""
Rewrite specs:
spec/functional_specs/policies/keycloak_role_check/client_roles/keycloak_client_combined_black_first_policy_spec.rb
spec/functional_specs/policies/keycloak_role_check/client_roles/keycloak_client_combined_white_first_policy_spec.rb
spec/functional_specs/policies/keycloak_role_check/realm_roles/keycloak_realm_combined_black_first_policy_spec.rb
spec/functional_specs/policies/keycloak_role_check/realm_roles/keycloak_realm_combined_white_first_policy_spec.rb
"""

import pytest
import pytest_cases
from pytest_cases import fixture_ref

from testsuite import rawobj
from testsuite.capabilities import Capability
from testsuite.utils import randomize
from .conftest import token

pytestmark = [pytest.mark.disruptive,
              pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY)]


@pytest_cases.fixture
def client_scope(application, client_role):
    """
    :return scope of policy for client role
    """

    def _client_scope(list_type: str):
        return {"client_roles": [{"name": client_role(randomize(f"client-role-{list_type}")),
                                  "client": application["client_id"]}]}

    return _client_scope


@pytest_cases.fixture
def realm_scope(realm_role):
    """
    :return scope of policy for client role
    """

    def _realm_scope(list_type: str):
        return {"realm_roles": [{"name": realm_role(randomize(f"realm-role-{list_type}"))}]}

    return _realm_scope


def policy_config_combined(list_type: str, scope: dict):
    """
    :return Configuration of keycloak policy
    """
    scopes1 = {"resource": f"/anything/{list_type}"}
    scopes1.update(scope)
    scopes2 = {"resource": "/anything/both"}
    scopes2.update(scope)
    configuration = {"type": list_type, "scopes": [scopes1, scopes2]}

    return rawobj.PolicyConfig("keycloak_role_check", configuration)


@pytest_cases.fixture
@pytest_cases.parametrize("scope", [fixture_ref(client_scope), fixture_ref(realm_scope)])
@pytest_cases.parametrize("first,second", [("whitelist", "blacklist"), ("blacklist", "whitelist")])
def config(service, scope, first, second):
    """
    Add keycloak policies to policy chain
    """
    service.proxy.list().policies.append(policy_config_combined(first, scope(first)))
    service.proxy.list().policies.append(policy_config_combined(second, scope(second)))


# pylint: disable=unused-argument
def test_combined(rhsso_service_info, application, config, create_users, prod_client):
    """
    Test if combined keycloak policy whitelist/blacklist path and user with client/realm role
    Test cases are same for client/realm role and whitelist/blacklist policy first
    Test cases:
        - request for path '/anything/white' + user_with_role status_code == 200
        - request for path '/anything/white' + user_without_role status_code == 403
        - request for path '/anything/both' + user_with_role status_code == 403
        - request for path '/anything/both' + user_without_role status_code == 403
        - request for path '/anything/black' + user_with_role status_code == 403
        - request for path '/anything/black' + user_without_role status_code == 403
        - request for path '/get' + user_with_role status_code == 403
        - request for path '/get' + user_without_role status_code == 403
    """
    user_with_role, user_without_role = create_users
    user_key_with_role = token(application, rhsso_service_info, user_with_role["username"])
    user_key_without_role = token(application, rhsso_service_info, user_without_role["username"])
    request = prod_client.get("/anything/whitelist", headers={'authorization': "Bearer " + user_key_with_role})
    assert request.status_code == 200
    request = prod_client.get("/anything/whitelist", headers={'authorization': "Bearer " + user_key_without_role})
    assert request.status_code == 403
    request = prod_client.get("/anything/both", headers={'authorization': "Bearer " + user_key_with_role})
    assert request.status_code == 403
    request = prod_client.get("/anything/both", headers={'authorization': "Bearer " + user_key_without_role})
    assert request.status_code == 403
    request = prod_client.get("/anything/blacklist", headers={'authorization': "Bearer " + user_key_with_role})
    assert request.status_code == 403
    request = prod_client.get("/anything/blacklist", headers={'authorization': "Bearer " + user_key_without_role})
    assert request.status_code == 403
    request = prod_client.get("/get", headers={'authorization': "Bearer " + user_key_with_role})
    assert request.status_code == 403
    request = prod_client.get("/get", headers={'authorization': "Bearer " + user_key_without_role})
    assert request.status_code == 403
