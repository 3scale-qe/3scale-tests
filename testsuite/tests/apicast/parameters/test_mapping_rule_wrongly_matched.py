"""
Test that URL with space in a parameter will be sent to the correct service when the
APICAST_PATH_ROUTING is in use
https://issues.redhat.com/browse/THREESCALE-4152
"""
import pytest

from testsuite.utils import blame
from testsuite import rawobj
from testsuite.gateways import TemplateApicastOptions, TemplateApicast


@pytest.fixture(scope="module")
def custom_route(request):
    """Returns randomized name of the custom route"""
    return blame(request, 'custom-route')


@pytest.fixture(scope="module")
def staging_gateway(configuration, request, custom_route):
    """
    Deploys template apicast gateway, configured not to create routes to services automatically.
    Sets the APICAST_PATH_ROUTING env variable to 1
    """
    settings_block = {
        "deployments": {
            "staging": blame(request, "path-routing-staging"),
            "production": blame(request, "path-routing-production")

        },
        "service_routes": False
    }
    options = TemplateApicastOptions(staging=True, settings_block=settings_block, configuration=configuration)
    gateway = TemplateApicast(requirements=options)
    gateway.create()

    gateway.set_env("APICAST_PATH_ROUTING", 1)
    gateway.add_route(custom_route, "custom-route")

    request.addfinalizer(gateway.destroy)
    return gateway


def delete_all_mapping_rules(proxy):
    """Deletes all mapping rules in a given proxy."""
    mapping_rules = proxy.mapping_rules.list()
    for mapping_rule in mapping_rules:
        proxy.mapping_rules.delete(mapping_rule["id"])


# pylint: disable=too-many-arguments
@pytest.fixture(scope="module")
def service(request, service_proxy_settings, private_base_url, custom_service, custom_route,
            staging_gateway):
    """
    Create a service using self managed apicast, sets the endpoint of the service to the custom
    route created in the gateway fixture.
    Sets mapping rule based on the tested bug.
    """
    service_proxy_settings["api_backend"] = private_base_url("echo_api")
    service = custom_service({"name": blame(request, "svc"),
                              "deployment_option": "self_managed"}, service_proxy_settings)

    metric = service.metrics.list()[0]
    proxy = service.proxy.list()

    delete_all_mapping_rules(proxy)
    proxy.mapping_rules.create(rawobj.Mapping(metric, "/foo/{anything}/bar"))

    proxy.update({"sandbox_endpoint": staging_gateway.endpoint % custom_route})

    return service


# pylint: disable=too-many-arguments
@pytest.fixture(scope="module")
def service2(request, service_proxy_settings, private_base_url, custom_service, custom_route,
             staging_gateway):
    """
    Create second service using self managed apicast, sets the endpoint of the service to the custom
    route created in the gateway fixture. The route is the same as for the first service as the
    apicast path routing is used.
    Sets mapping rule based on the tested bug.
    """
    service_proxy_settings["api_backend"] = private_base_url("echo_api")
    service2 = custom_service({"name": blame(request, "svc"),
                               "deployment_option": "self_managed"}, service_proxy_settings)

    metric = service2.metrics.list()[0]
    proxy = service2.proxy.list()

    delete_all_mapping_rules(proxy)
    proxy.mapping_rules.create(rawobj.Mapping(metric, "/ip/{anything}"))

    proxy.update({"sandbox_endpoint": staging_gateway.endpoint % custom_route})

    return service2


# pylint: disable=unused-argument
def test_mapping_rule_wrongly_matched(service2, api_client):
    """
    service2 has to be created before service

    Makes a request to an endpoint containing a space char.
    Asserts that the response is not "no mapping rule matched"
    """
    response = api_client.get("/foo/123 123/bar")
    assert response.status_code == 200
