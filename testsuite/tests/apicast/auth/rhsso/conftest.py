"""
Conftest for the rhsso tests
"""

import pytest

from testsuite.rhsso.rhsso import OIDCClientAuthHook


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(lifecycle_hooks, rhsso_service_info):
    """Have application/service with RHSSO auth configured"""

    lifecycle_hooks.append(OIDCClientAuthHook(rhsso_service_info))
    return rhsso_service_info


@pytest.fixture(scope="module", autouse=True)
def allow_full_scope(rhsso_setup, application):
    """
    Sets fullScopeAllowed as True for newly registered clients.
    fullScopeAllowed allows all access tokens to contain all roles held by user.
    Required for RHSSO testing.
    """
    client_uuid = rhsso_setup.get_application_client(application)
    rhsso_setup.realm.admin.update_client(client_uuid, {"fullScopeAllowed": True})
