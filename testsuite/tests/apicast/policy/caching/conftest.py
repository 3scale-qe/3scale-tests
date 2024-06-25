"""Module containing all caching tests"""

import pytest

from testsuite.gateways import gateway
from testsuite.gateways.apicast.selfmanaged import SelfManagedApicast
from testsuite.gateways.gateways import Capability
from testsuite.utils import blame


@pytest.fixture(
    scope="module",
    params=[
        pytest.param(
            None,
            marks=[
                pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY),
                pytest.mark.required_capabilities(Capability.OCP3),
                pytest.mark.disruptive,
            ],
            id="Default gateway",
        ),
        pytest.param(
            SelfManagedApicast,
            marks=[pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY), pytest.mark.disruptive],
            id="Self-managed gateway",
        ),
    ],
)
def production_gateway(request, testconfig):
    """Production gateway for caching tests"""
    gw = gateway(kind=request.param, staging=False, name=blame(request, "production"))
    if not testconfig["skip_cleanup"]:
        request.addfinalizer(gw.destroy)
    gw.create()

    return gw


# pylint: disable=too-many-arguments, unused-argument
@pytest.fixture(scope="module")
def service(
    request,
    backends_mapping,
    custom_service,
    production_gateway,
    service_proxy_settings,
    lifecycle_hooks,
    policy_settings,
):
    """
    Preconfigured service, which is created for each policy settings, which are often parametrized in this module
    Production gateway dependency is needed due to needing different services for each gateway
    """
    service = custom_service(
        {"name": blame(request, "svc")}, service_proxy_settings, backends_mapping, hooks=lifecycle_hooks
    )
    if policy_settings:
        service.proxy.list().policies.append(policy_settings)
    return service
