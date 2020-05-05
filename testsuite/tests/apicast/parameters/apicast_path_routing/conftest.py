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
def service(service):
    """Delete mapping rules and add new one from/to default service."""
    proxy = service.proxy.list()
    metric = service.metrics.list()[0]

    delete_all_mapping_rules(proxy)

    proxy.mapping_rules.create(rawobj.Mapping(metric, "/get"))
    proxy.update()

    return service


@pytest.fixture(scope="module")
def service2_proxy_settings(private_base_url, service_proxy_settings):
    """Change api_backend to echo-api for service2."""
    service_proxy_settings["api_backend"] = private_base_url("echo-api")
    return service_proxy_settings


@pytest.fixture(scope="module")
def service2(request, service2_proxy_settings, custom_service):
    """Create second service and mapping rule."""
    service2 = custom_service({"name": blame(request, "svc")}, service2_proxy_settings)

    metric = service2.metrics.list()[0]
    proxy = service2.proxy.list()

    delete_all_mapping_rules(proxy)

    proxy.mapping_rules.create(rawobj.Mapping(metric, "/echo"))
    proxy.update()

    return service2


@pytest.fixture(scope="module")
def application2(service2, custom_app_plan, custom_application, request):
    """Create custom application for service2."""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service2)
    return custom_application(rawobj.Application(blame(request, "app"), plan))


@pytest.fixture(scope="module")
def api_client2(application2):
    """Client for second application."""
    return application2.api_client()
