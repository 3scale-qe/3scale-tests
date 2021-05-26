"""
Rewrite of the spec/functional_specs/auth/rhsso/open_id_rhsso_zync_sync_spec.rb
"""
import backoff
import pytest

from testsuite.rhsso.rhsso import OIDCClientAuthHook


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(lifecycle_hooks, rhsso_service_info):
    """Have application/service with RHSSO auth configured"""

    lifecycle_hooks.append(OIDCClientAuthHook(rhsso_service_info))


# Zync is sometimes too slow to create the RHSSO client.
@backoff.on_predicate(backoff.fibo, lambda x: x is None, 8, jitter=None)
def get_rhsso_client(application, rhsso_service_info):
    """
    Retries until the RHSSO client is created
    :param application: application
    :param rhsso_service_info: RHSSO service info
    :return: RHSSO client
    """
    return rhsso_service_info.realm.clients.by_client_id(application["client_id"])


def test_rhsso_zync_sync(application, rhsso_service_info):
    """Test checks if the RHSSO client is created with correct fields such as:
        - name
        - client id
        - client secret
    """
    rhsso_client = get_rhsso_client(application, rhsso_service_info)
    assert rhsso_client is not None

    assert rhsso_client.name == application['name']
    assert rhsso_client.clientId == application['client_id']
    assert rhsso_client.secret.get('value', '') == application['client_secret']
