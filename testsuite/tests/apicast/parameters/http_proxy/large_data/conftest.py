"""Conftest for http proxy large data tests"""
import pytest

from testsuite import rawobj
from testsuite.utils import blame


# TODO: add HTTP protocol
#  Right now the HTTP protocol doesn't work with tinyproxy and HTTP openshift route.
#  Workaround is to use hostname of the openshift service of HTTPBIN.
@pytest.fixture(scope="module", params=["https"])
def protocol(request):
    """Protocol which is used on http(s) service/proxy/backend"""
    return request.param


@pytest.fixture(scope="module")
def settings_block(settings_block, configuration, protocol):
    """Settings block with http(s) endpoints"""
    endpoints = {"staging_endpoint": f"{protocol}://%s-staging.{configuration.superdomain}",
                 "production_endpoint": f"{protocol}://%s-staging.{configuration.superdomain}"}
    settings_block.update(endpoints)
    return settings_block


@pytest.fixture(scope="module")
def gateway_environment(gateway_environment, testconfig):
    """Adds HTTP proxy to the staging gateway"""
    proxy_endpoint = testconfig["proxy"]

    gateway_environment.update({"HTTP_PROXY": proxy_endpoint['http'],
                                "HTTPS_PROXY": proxy_endpoint['https'],
                                "NO_PROXY": "backend-listener,system-master"})
    return gateway_environment


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
    service.proxy.list().update()
    return service
