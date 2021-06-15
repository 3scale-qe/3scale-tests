"""
Rewrite of the spec/functional_specs/auth/rhsso/open_id_rhsso_zync_sync_spec.rb
"""
import backoff
import pytest
from keycloak import KeycloakGetError

from testsuite.rhsso import OIDCClientAuthHook


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(lifecycle_hooks, rhsso_service_info):
    """Have application/service with RHSSO auth configured"""

    lifecycle_hooks.append(OIDCClientAuthHook(rhsso_service_info))


# Zync is sometimes too slow to create the RHSSO client.
@backoff.on_exception(backoff.fibo, KeycloakGetError, 8, jitter=None)
def get_rhsso_client(application, rhsso_service_info):
    """
    Retries until the RHSSO client is created
    :param application: application
    :param rhsso_service_info: RHSSO service info
    :return: RHSSO client
    """
    client_id = rhsso_service_info.get_application_client(application)
    client = rhsso_service_info.realm.admin.get_client(client_id)
    secrets = rhsso_service_info.realm.admin.get_client_secrets(client_id)
    return client, secrets


def test_rhsso_zync_sync(application, rhsso_service_info):
    """Test checks if the RHSSO client is created with correct fields such as:
        - name
        - client id
        - client secret
    """
    rhsso_client, secrets = get_rhsso_client(application, rhsso_service_info)
    assert rhsso_client is not None

    assert rhsso_client["name"] == application['name']
    assert rhsso_client["clientId"] == application['client_id']
    assert secrets["value"] == application['client_secret']
