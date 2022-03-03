"""
Test for using OIDC with apicast env_variable 'APICAST_SERVICES_FILTER_BY_URL' and 'APICAST_PATH_ROUTING'
"""
import pytest

from testsuite import rawobj
from testsuite.gateways import gateway
from testsuite.capabilities import Capability
from testsuite.gateways.apicast.template import TemplateApicast
from testsuite.rhsso.rhsso import OIDCClientAuthHook
from testsuite.utils import blame

pytestmark = [pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.PRODUCTION_GATEWAY,
                                                Capability.CUSTOM_ENVIRONMENT)]


@pytest.fixture(scope="module")
def gateway_kind():
    """Gateway class to use for tests"""
    return TemplateApicast


@pytest.fixture(scope="module")
def production_gateway(request, gateway_environment):
    """Deploy self-managed template based apicast gateway."""
    gw = gateway(kind=TemplateApicast, staging=False, name=blame(request, "gw"))
    request.addfinalizer(gw.destroy)
    gw.create()

    if len(gateway_environment) > 0:
        gw.environ.set_many(gateway_environment)

    return gw


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(lifecycle_hooks, rhsso_service_info):
    """Have application/service with RHSSO auth configured"""

    lifecycle_hooks.append(OIDCClientAuthHook(rhsso_service_info))


@pytest.fixture(scope="module")
def service_mapping():
    """Change mapping rule for service"""
    return "/anything/foo"


@pytest.fixture(scope="module")
def service2_mapping():
    """Change mapping rule for service2"""
    return "/anything/bar"


@pytest.fixture(scope="module")
def gateway_environment(gateway_environment):
    """Setup ENV variables for apicast"""
    gateway_environment.update({"APICAST_SERVICES_FILTER_BY_URL": ".*",
                                "APICAST_PATH_ROUTING": "true",
                                "APICAST_PATH_ROUTING_ONLY": "true",
                                "APICAST_CONFIGURATION_CACHE": "-1",
                                "APICAST_MANAGEMENT_API": "debug",
                                "APICAST_LOG_LEVEL": "debug",
                                "APICAST_OIDC_LOG_LEVEL": "debug"
                                })
    return gateway_environment


@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url):
    """Change api_backend to httpbin for service."""
    return rawobj.Proxy(private_base_url("httpbin"))


# pylint: disable=unused-argument
def test_filter_by_url(application, application2, production_gateway, prod_client):
    """
    Send request to first service using rhsso OIDC authentication
    Send request to second service using rhsso OIDC authentication

    Assert that both requests have status_code == 200
    """

    api_client1 = prod_client(application, redeploy=False)
    api_client2 = prod_client(application2)

    request = api_client1.get("/anything/foo")
    assert request.status_code == 200

    request = api_client2.get("/anything/bar")
    assert request.status_code == 200
