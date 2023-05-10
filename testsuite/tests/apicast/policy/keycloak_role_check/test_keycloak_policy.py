"""
Rewrite specs:
spec/functional_specs/policies/keycloak_role_check/client_roles/keycloak_client_blacklist_method_spec.rb
spec/functional_specs/policies/keycloak_role_check/client_roles/keycloak_client_blacklist_policy_spec.rb
spec/functional_specs/policies/keycloak_role_check/client_roles/keycloak_client_whitelist_method_spec.rb
spec/functional_specs/policies/keycloak_role_check/client_roles/keycloak_client_whitelist_policy_spec.rb
spec/functional_specs/policies/keycloak_role_check/realm_roles/keycloak_realm_blacklist_method_spec.rb
spec/functional_specs/policies/keycloak_role_check/realm_roles/keycloak_realm_blacklist_policy_spec.rb
spec/functional_specs/policies/keycloak_role_check/realm_roles/keycloak_realm_whitelist_method_spec.rb
spec/functional_specs/policies/keycloak_role_check/realm_roles/keycloak_realm_whitelist_policy_spec.rb
"""

import pytest
import pytest_cases
from pytest_cases import fixture_ref

from testsuite import rawobj
from testsuite.capabilities import Capability
from .conftest import token

pytestmark = [pytest.mark.disruptive, pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY)]


@pytest_cases.fixture
def client_scope(application, client_role):
    """
    :return scope of policy for client role
    """
    return {"client_roles": [{"name": client_role(), "client": application["client_id"]}]}


@pytest_cases.fixture
def realm_scope(realm_role):
    """
    :return scope of policy for client role
    """
    return {"realm_roles": [{"name": realm_role()}]}


def policy_config(list_type: str, scope: dict, method: dict):
    """
    :return Configuration of keycloak policy
    """
    scopes = {"resource": f"/anything/{list_type}"}
    scopes.update(scope)
    scopes.update(method)
    configuration = {"type": list_type, "scopes": [scopes]}

    return rawobj.PolicyConfig("keycloak_role_check", configuration)


# pylint: disable=too-many-arguments
@pytest_cases.fixture
@pytest_cases.parametrize("list_type,code1,code2", [("whitelist", 200, 403), ("blacklist", 403, 200)])
@pytest_cases.parametrize("scope", [fixture_ref(client_scope), fixture_ref(realm_scope)])
@pytest_cases.parametrize("method", [{}, {"methods": ["GET"]}])
def config(service, list_type, scope, method, code1, code2):
    """
    Add keycloak policy to policy chain
    """
    service.proxy.list().policies.append(policy_config(list_type, scope, method))
    return list_type, method, code1, code2


def test_separated(rhsso_service_info, application, config, create_users, prod_client):
    """
    Test if keycloak policy whitelist/blacklist path,user with client/realm role and method
    Test cases are the same for client and realm role
    Whitelist:
        - request for path '/anything/white' + user_with_role status_code == 200
        - request for path '/anything/white' + user_without_role status_code == 403
        - request for path '/get' + user_with_role status_code == 403
        - request for path '/get' + user_without_role status_code == 403
        Method:
         - POST request for path '/anything/white' + user_with_role status_code == 403
         - POST request for path 'post' + user_with_role status_code == 403

     Blacklist:
        - request for path '/anything/black' + user_with_role status_code == 403
        - request for path '/anything/black' + user_without_role status_code == 200
        - request for path '/get' + user_with_role status_code == 200
        - request for path '/get' + user_without_role status_code == 200
        Method:
         - request for path '/anything/black' + user_with_role status_code == 200
         - request for path '/post' + user_with_role status_code == 200
    """
    list_type, method, code1, code2 = config
    user_with_role, user_without_role = create_users
    user_key_with_role = token(application, rhsso_service_info, user_with_role["username"])
    user_key_without_role = token(application, rhsso_service_info, user_without_role["username"])
    request = prod_client.get(f"/anything/{list_type}", headers={"authorization": "Bearer " + user_key_with_role})
    assert request.status_code == code1
    request = prod_client.get(f"/anything/{list_type}", headers={"authorization": "Bearer " + user_key_without_role})
    assert request.status_code == code2
    request = prod_client.get("/get", headers={"authorization": "Bearer " + user_key_with_role})
    assert request.status_code == code2
    request = prod_client.get("/get", headers={"authorization": "Bearer " + user_key_without_role})
    assert request.status_code == code2
    if method != {}:
        request = prod_client.post(f"/anything/{list_type}", headers={"authorization": "Bearer " + user_key_with_role})
        assert request.status_code == code2
        request = prod_client.post("/post", headers={"authorization": "Bearer " + user_key_with_role})
        assert request.status_code == code2
