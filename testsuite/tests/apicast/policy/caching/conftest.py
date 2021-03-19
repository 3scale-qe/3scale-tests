"""Module containing all caching tests"""
import pytest

from testsuite import gateways
from testsuite.gateways import TemplateApicastOptions, TemplateApicast
from testsuite.gateways.gateways import Capability
from testsuite.utils import blame


@pytest.fixture(scope="module")
def custom_gateway(request, configuration):
    """Deploy template apicast gateway."""

    options = TemplateApicastOptions(staging=False, settings_block={
        "deployments": {
            "staging": blame(request, "staging"),
            "production": blame(request, "production")
        }
    }, configuration=configuration)
    gateway = TemplateApicast(requirements=options)

    request.addfinalizer(gateway.destroy)

    gateway.create()

    return gateway


@pytest.fixture(scope="module")
def default_gateway(request, testconfig, configuration):
    """Staging gateway"""
    options = gateways.configuration.options(staging=False,
                                             settings_block=testconfig["threescale"]["gateway"]["configuration"],
                                             configuration=configuration)
    gateway = gateways.configuration.production(options)
    request.addfinalizer(gateway.destroy)

    gateway.create()

    return gateway


@pytest.fixture(scope="module", params=[
    pytest.param("default_gateway", marks=[
        pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY),
        pytest.mark.required_capabilities(Capability.OCP3),
        pytest.mark.disruptive
    ]),
    pytest.param("custom_gateway", marks=[
        pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY),
        pytest.mark.disruptive
    ])
])
def production_gateway(request):
    """Production gateway for chacing tests"""
    return request.getfixturevalue(request.param)


# pylint: disable=too-many-arguments, unused-argument
@pytest.fixture(scope="module")
def service(request, backends_mapping, custom_service, production_gateway,
            service_proxy_settings, lifecycle_hooks, policy_settings):
    """
    Preconfigured service, which is created for each policy settings, which are often parametrized in this module
    Production gateway dependency is needed due to needing different services for each gateway
    """
    service = custom_service({"name": blame(request, "svc")}, service_proxy_settings, backends_mapping,
                             hooks=lifecycle_hooks)
    if policy_settings:
        service.proxy.list().policies.append(policy_settings)
    return service
