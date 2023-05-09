"""Path routing-based tests fixtures."""
import pytest

from testsuite import rawobj
from testsuite.utils import blame


def delete_all_mapping_rules(proxy):
    """Deletes all mapping rules in a given proxy."""
    mapping_rules = proxy.mapping_rules.list()
    for mapping_rule in mapping_rules:
        proxy.mapping_rules.delete(mapping_rule["id"])


@pytest.fixture(scope="module")
def gateway_options(gateway_options):
    """Deploy template apicast staging gateway."""
    gateway_options["path_routing"] = True

    return gateway_options


@pytest.fixture(scope="module")
def service_mapping():
    """Change mapping rule for service"""
    return "/get"


@pytest.fixture(scope="module")
def service(service, service_mapping):
    """Delete mapping rules and add new one from/to default service."""
    proxy = service.proxy.list()
    metric = service.metrics.list()[0]

    delete_all_mapping_rules(proxy)

    proxy.mapping_rules.create(rawobj.Mapping(metric, service_mapping))
    proxy.update()

    return service


@pytest.fixture(scope="module")
def service2_proxy_settings(private_base_url):
    """Change api_backend to echo-api for service2."""
    return rawobj.Proxy(private_base_url("echo_api"))


@pytest.fixture(scope="module")
def service2_mapping():
    """Change mapping rule for service2"""
    return "/echo"


# pylint: disable=too-many-arguments
@pytest.fixture(scope="module")
def service2(request, custom_service, lifecycle_hooks, service2_proxy_settings, service2_mapping):
    """Create second service and mapping rule."""
    service2 = custom_service({"name": blame(request, "svc")}, service2_proxy_settings, hooks=lifecycle_hooks)

    metric = service2.metrics.list()[0]
    proxy = service2.proxy.list()

    delete_all_mapping_rules(proxy)
    proxy.mapping_rules.create(rawobj.Mapping(metric, service2_mapping))
    proxy.update()

    return service2


@pytest.fixture(scope="module")
def application2(request, service2, custom_app_plan, custom_application, lifecycle_hooks):
    """Create custom application for service2."""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service2)
    return custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)


@pytest.fixture(scope="module")
def client(api_client):
    """Client for the first application."""
    return api_client()


@pytest.fixture(scope="module")
def client2(application2, api_client):
    """Client for second application."""
    return api_client(application2)
