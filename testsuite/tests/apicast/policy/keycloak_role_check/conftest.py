"""
Conftest for keycloak policy
"""

import pytest_cases

from testsuite import rawobj
from testsuite.rhsso.rhsso import OIDCClientAuthHook
from testsuite.utils import randomize, blame


# pylint: disable=unused-argument
@pytest_cases.fixture
def service(rhsso_setup, service_proxy_settings, custom_service, lifecycle_hooks, request):
    """Service configured with config"""
    service = custom_service({"name": blame(request, "svc")}, service_proxy_settings, hooks=lifecycle_hooks)

    proxy = service.proxy.list()
    metric = service.metrics.list()[0]
    proxy.mapping_rules.create(rawobj.Mapping(metric=metric, http_method="POST"))
    proxy.deploy()

    return service


# pylint: disable=unused-argument, too-many-arguments
@pytest_cases.fixture
def application(rhsso_setup, service, custom_application, custom_app_plan, lifecycle_hooks, request):
    """application bound to the account and service existing over whole testing session"""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    return custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)


@pytest_cases.fixture(scope="module")
def rhsso_setup(lifecycle_hooks, rhsso_service_info):
    """Have application/service with RHSSO auth configured"""

    lifecycle_hooks.append(OIDCClientAuthHook(rhsso_service_info))


@pytest_cases.fixture
def create_users(rhsso_service_info):
    """
    Create 2 rhsso users
    """
    realm = rhsso_service_info.realm
    user_with_role = realm.create_user(randomize("user_with_role"), rhsso_service_info.password)
    user_without_role = realm.create_user(randomize("user_without_role"), rhsso_service_info.password)

    user_with_role = realm.admin.get_user(user_with_role)
    user_without_role = realm.admin.get_user(user_without_role)

    return user_with_role, user_without_role


@pytest_cases.fixture
def client_role(application, rhsso_service_info, create_users):
    """
    Create client role and add it to user_with_role
    """

    def _client_role(role_name=randomize("client-role")):
        user_with_role, _ = create_users
        client = get_rhsso_client(application, rhsso_service_info)
        admin = rhsso_service_info.realm.admin

        admin.create_client_role(client, {"name": role_name})
        role = admin.get_client_role(client, role_name)
        admin.assign_client_role(user_with_role["id"], client, role)
        return role_name

    return _client_role


@pytest_cases.fixture
def realm_role(rhsso_service_info, create_users):
    """
    Create realm role and add it to user_with_role
    """

    def _realm_role(role_name=None):
        role_name = role_name or randomize("realm-role")
        user_with_role, _ = create_users

        admin = rhsso_service_info.realm.admin
        admin.create_realm_role({"name": role_name})
        role = admin.get_realm_role(role_name)
        admin.assign_realm_roles(user_with_role["id"], role)
        return role_name

    return _realm_role


@pytest_cases.fixture()
def prod_client(application, production_gateway):
    """
    Prepares application and service for production use and creates new production client
    :return Api client for application
    """
    version = application.service.proxy.list().configs.latest()["version"]
    application.service.proxy.list().promote(version=version)
    production_gateway.reload()

    client = application.api_client(endpoint="endpoint")

    client.auth = None
    return client


# Zync is sometimes too slow to create the RHSSO client.
def get_rhsso_client(application, rhsso_service_info):
    """
    Retries until the RHSSO client is created
    :param application: application
    :param rhsso_service_info: RHSSO service info
    :return: RHSSO client
    """
    return rhsso_service_info.get_application_client(application)


def token(application, rhsso_service_info, username):
    """Access token for 3scale application that is connected with RHSSO"""
    app_key = application.keys.list()[-1]["value"]
    return rhsso_service_info.password_authorize(application["client_id"], app_key, username)["access_token"]
