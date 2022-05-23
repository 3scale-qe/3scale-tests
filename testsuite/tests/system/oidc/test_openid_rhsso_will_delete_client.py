"""
Rewrite of spec/functional_specs/auth/rhsso/open_id_rhsso_will_delete_client_spec.rb
"""

import backoff
import pytest
from keycloak.exceptions import KeycloakGetError

from testsuite import rawobj
from testsuite.rhsso import OIDCClientAuthHook
from testsuite.utils import randomize

pytestmark = [pytest.mark.nopersistence]


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(lifecycle_hooks, rhsso_service_info):
    """Have application/service with RHSSO auth configured"""

    lifecycle_hooks.append(OIDCClientAuthHook(rhsso_service_info))


@pytest.fixture(scope="module")
def application(service, custom_application, custom_app_plan, lifecycle_hooks):
    """application bound to the account and service existing over whole testing session"""
    plan = custom_app_plan(rawobj.ApplicationPlan(randomize("AppPlan")), service)
    return custom_application(rawobj.Application(randomize("App"), plan), autoclean=False, hooks=lifecycle_hooks)


# Zync is sometimes too slow to create the RHSSO client.
@backoff.on_predicate(backoff.fibo, lambda x: x is None, max_tries=8, jitter=None)
def get_rhsso_client(application, rhsso_service_info):
    """
    Retries until the RHSSO client is created
    :param application: application
    :param rhsso_service_info: RHSSO service info
    :return: RHSSO client
    """
    return rhsso_service_info.get_application_client(application)


# Zync is sometimes too slow to delete the RHSSO client.
@backoff.on_predicate(backoff.fibo, lambda x: x is not None, max_tries=8, jitter=None)
def check_deleted_client(client_id, rhsso_service_info):
    """
    Retries until the RHSSO client is deleted
    :param client_id: client_id of the deleted application
    :param rhsso_service_info: RHSSO service info
    :return: RHSSO client
    """
    try:
        rhsso_service_info.realm.admin.get_client(client_id)
    except KeycloakGetError:
        return True

    raise ValueError("Client still exists")


def test_rhsso_client_delete(application, rhsso_service_info):
    """Test checks if the RHSSO client is deleted when 3scale application is deleted"""
    assert get_rhsso_client(application, rhsso_service_info) is not None
    client_id = application['client_id']
    application.delete()

    assert check_deleted_client(client_id, rhsso_service_info)
