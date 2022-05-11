"""Tests that APICAST_LOAD_SERVICES_WHEN_NEEDED loads all mapping rules"""
import pytest

from testsuite import rawobj
from testsuite.capabilities import Capability

from testsuite.gateways.apicast.selfmanaged import SelfManagedApicast
from testsuite.utils import blame

pytestmark = [
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-8419")
]


@pytest.fixture(scope="module")
def gateway_kind():
    """Gateway class to use for tests"""
    return SelfManagedApicast


@pytest.fixture(scope="module")
def service(backends_mapping, custom_service, service_proxy_settings, lifecycle_hooks, request):
    """
        Creates service and adds mapping for POST method with path /
        We need to create the service here because there will be 2 services created and they cannot have the same name
    """
    service = custom_service({"name": blame(request, "svc")},
                             service_proxy_settings, backends_mapping, hooks=lifecycle_hooks)
    metric = service.metrics.list()[0]
    service.proxy.list().mapping_rules.create(rawobj.Mapping(metric, "/", "POST"))
    service.proxy.deploy()
    return service


@pytest.mark.parametrize("load_service", [
    pytest.param(True, marks=pytest.mark.xfail),
    False
])
def test_mapping_rule_hit(api_client, staging_gateway, load_service):
    """Tests that the mapping rule is loaded and works correctly"""
    staging_gateway.environ["APICAST_LOAD_SERVICES_WHEN_NEEDED"] = load_service

    client = api_client()

    response = client.post('/post')
    assert response.status_code == 200
