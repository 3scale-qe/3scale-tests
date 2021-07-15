"""
Conftest for the liquid context debug policy
"""
import pytest

from testsuite import rawobj
from testsuite.rhsso.rhsso import OIDCClientAuthHook


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(lifecycle_hooks, rhsso_service_info):
    """Have application/service with RHSSO auth configured"""

    lifecycle_hooks.append(OIDCClientAuthHook(rhsso_service_info, "query"))


@pytest.fixture(scope="module")
def service(service):
    "Service with prepared policy_settings added"
    service.proxy.list().policies.insert(0, rawobj.PolicyConfig("liquid_context_debug", {}))
    return service


@pytest.fixture(scope="module")
def access_token(application, rhsso_service_info):
    """get rhsso access token"""
    app_key = application.keys.list()["keys"][0]["key"]["value"]
    return rhsso_service_info.password_authorize(application["client_id"],
                                                 app_key).token['access_token']
