"""
Conftest for keycloak policy
"""

import backoff
from pytest_cases import fixture_plus

from testsuite import rawobj
from testsuite.rhsso.rhsso import OIDCClientAuthHook
from testsuite.utils import randomize, blame


# pylint: disable=unused-argument
@fixture_plus
def service(rhsso_setup, service_proxy_settings, custom_service, lifecycle_hooks, request):
    """Service configured with config"""
    service = custom_service({"name": blame(request, "svc")}, service_proxy_settings, hooks=lifecycle_hooks)

    proxy = service.proxy.list()
    metric = service.metrics.list()[0]
    proxy.mapping_rules.create(rawobj.Mapping(metric=metric, http_method="POST"))
    proxy.deploy()

    return service


# pylint: disable=unused-argument, too-many-arguments
@fixture_plus
def application(rhsso_setup, service, custom_application, custom_app_plan, lifecycle_hooks, request):
    """application bound to the account and service existing over whole testing session"""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    return custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)


@fixture_plus
def rhsso_setup(lifecycle_hooks, rhsso_service_info):
    """Have application/service with RHSSO auth configured"""

    lifecycle_hooks.append(OIDCClientAuthHook(rhsso_service_info))


@fixture_plus
def create_users(rhsso_service_info):
    """
    Create 2 rhsso users
    """
    realm = rhsso_service_info.realm
    user_with_role = realm.users.create(randomize("user_with_role"), enabled=True)
    user_with_role.reset_password("testUser", temporary=False)
    user_without_role = realm.users.create(randomize("user_without_role"), enabled=True)
    user_without_role.reset_password("testUser", temporary=False)
    return user_with_role, user_without_role


@fixture_plus
def client_role(application, rhsso_service_info, create_users):
    """
    Create client role and add it to user_with_role
    """

    def _client_role(role_name=randomize("client-role")):
        user_with_role, _ = create_users
        client = get_rhsso_client(application, rhsso_service_info)
        client.roles.create(role_name)
        role = client.roles.by_name(role_name)
        user_with_role.role_mappings.client(client).add([role.entity])
        return role_name

    return _client_role


@fixture_plus
def realm_role(rhsso_service_info, create_users):
    """
    Create realm role and add it to user_with_role
    """

    def _realm_role(role_name=randomize("realm-role")):
        user_with_role, _ = create_users
        realm = rhsso_service_info.realm
        realm.roles.create(role_name)
        role = realm.roles.by_name(role_name)
        user_with_role.role_mappings.realm.add([role.entity])
        return role_name

    return _realm_role


@fixture_plus()
def prod_client(application, production_gateway):
    """
    Prepares application and service for production use and creates new production client
    :return Api client for application
    """
    version = application.service.proxy.list().configs.latest()['version']
    application.service.proxy.list().promote(version=version)
    production_gateway.reload()

    client = application.api_client(endpoint="endpoint")

    # pylint: disable=protected-access
    client._session.auth = None
    return client


# Zync is sometimes too slow to create the RHSSO client.
@backoff.on_predicate(backoff.constant, lambda x: x is None, 60)
def get_rhsso_client(application, rhsso_service_info):
    """
    Retries until the RHSSO client is created
    :param application: application
    :param rhsso_service_info: RHSSO service info
    :return: RHSSO client
    """
    return rhsso_service_info.realm.clients.by_client_id(application["client_id"])


def token(application, rhsso_service_info, username):
    """Access token for 3scale application that is connected with RHSSO"""
    app_key = application.keys.list()["keys"][0]["key"]["value"]
    auth = rhsso_service_info.rhsso.password_authorize(rhsso_service_info.realm, application["client_id"], app_key,
                                                       username, "testUser")
    return auth.token['access_token']
