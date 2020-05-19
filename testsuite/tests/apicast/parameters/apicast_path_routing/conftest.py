"""Path routing-based tests fixtures."""
import pytest

from testsuite import rawobj
from testsuite.gateways import TemplateApicastOptions, TemplateApicast
from testsuite.utils import blame


def delete_all_mapping_rules(proxy):
    """Deletes all mapping rules in a given proxy."""
    mapping_rules = proxy.mapping_rules.list()
    for mapping_rule in mapping_rules:
        proxy.mapping_rules.delete(mapping_rule["id"])


@pytest.fixture(scope="module")
def route_name(request):
    """Returns randomized name of path-routing route"""
    return blame(request, 'path-routing')


@pytest.fixture(scope="module")
def staging_gateway(request, configuration, route_name):
    """Deploy template apicast gateway."""
    settings_block = {
        "deployments": {
            "staging": blame(request, "path-routing"),
            "production": blame(request, "path-routing")
        },
        "service_routes": False,
    }
    options = TemplateApicastOptions(staging=True, settings_block=settings_block, configuration=configuration)
    gateway = TemplateApicast(requirements=options)
    gateway.create()

    gateway.add_route(route_name)

    request.addfinalizer(gateway.destroy)

    return gateway


@pytest.fixture(scope="module")
def endpoint(staging_gateway, route_name):
    """Returns gateway endpoint."""
    return staging_gateway.endpoint % route_name


@pytest.fixture(scope="module")
def service(service, endpoint):
    """Delete mapping rules and add new one from/to default service."""
    proxy = service.proxy.list()
    metric = service.metrics.list()[0]

    delete_all_mapping_rules(proxy)

    proxy.mapping_rules.create(rawobj.Mapping(metric, "/get"))

    proxy.update({"sandbox_endpoint": endpoint})

    return service


@pytest.fixture(scope="module")
def service2_proxy_settings(private_base_url):
    """Change api_backend to echo-api for service2."""
    return rawobj.Proxy(private_base_url("echo-api"))


@pytest.fixture(scope="module")
def service2(request, custom_service, lifecycle_hooks, service2_proxy_settings, endpoint):
    """Create second service and mapping rule."""
    service2 = custom_service({"name": blame(request, "svc")}, service2_proxy_settings,
                              hooks=lifecycle_hooks)

    metric = service2.metrics.list()[0]
    proxy = service2.proxy.list()

    delete_all_mapping_rules(proxy)

    proxy.mapping_rules.create(rawobj.Mapping(metric, "/echo"))

    proxy.update({"sandbox_endpoint": endpoint})

    return service2


@pytest.fixture(scope="module")
def application2(request, service2, custom_app_plan, custom_application, lifecycle_hooks):
    """Create custom application for service2."""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service2)
    return custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)


@pytest.fixture(scope="module")
def api_client2(application2):
    """Client for second application."""
    return application2.api_client()
