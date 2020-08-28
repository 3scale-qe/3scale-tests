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

from pytest_cases import fixture_plus, parametrize_plus, fixture_ref

from testsuite import rawobj
from testsuite.gateways.gateways import Capability
from .conftest import get_rhsso_client, token


pytestmark = [pytest.mark.disruptive,
              pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY)]


@fixture_plus
def client_scope(application, rhsso_service_info, client_role):
    """
    :return scope of policy for client role
    """
    client = get_rhsso_client(application, rhsso_service_info).entity["clientId"]
    return {"client_roles": [{"name": client_role(), "client": client}]}


@fixture_plus
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
@fixture_plus
@parametrize_plus("list_type,code1,code2", [("whitelist", 200, 403), ("blacklist", 403, 200)])
@parametrize_plus("scope", [fixture_ref(client_scope), fixture_ref(realm_scope)])
@parametrize_plus("method", [{}, {"methods": ["GET"]}])
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
    user_key_with_role = token(application, rhsso_service_info, user_with_role.entity["username"])
    user_key_without_role = token(application, rhsso_service_info, user_without_role.entity["username"])
    request = prod_client.get(f"/anything/{list_type}", headers={'authorization': "Bearer " + user_key_with_role})
    assert request.status_code == code1
    request = prod_client.get(f"/anything/{list_type}", headers={'authorization': "Bearer " + user_key_without_role})
    assert request.status_code == code2
    request = prod_client.get("/get", headers={'authorization': "Bearer " + user_key_with_role})
    assert request.status_code == code2
    request = prod_client.get("/get", headers={'authorization': "Bearer " + user_key_without_role})
    assert request.status_code == code2
    if method != {}:
        request = prod_client.post(f"/anything/{list_type}", headers={'authorization': "Bearer " + user_key_with_role})
        assert request.status_code == code2
        request = prod_client.post("/post", headers={'authorization': "Bearer " + user_key_with_role})
        assert request.status_code == code2
