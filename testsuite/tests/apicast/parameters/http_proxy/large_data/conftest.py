"""Conftest for http proxy large data tests"""
from urllib.parse import urlparse

import pytest

from testsuite import rawobj
from testsuite.gateways.apicast.selfmanaged import SelfManagedApicast
from testsuite.utils import blame


# TODO: add HTTP protocol
#  Right now the HTTP protocol doesn't work with tinyproxy and HTTP openshift route.
#  Workaround is to use hostname of the openshift service of HTTPBIN.
@pytest.fixture(scope="module", params=["https"])
def protocol(request):
    """Protocol which is used on http(s) service/proxy/backend"""
    return request.param


@pytest.fixture(scope="module")
def gateway_kind():
    """Gateway class to use for tests"""
    return SelfManagedApicast


@pytest.fixture(scope="module")
def gateway_environment(gateway_environment, testconfig, tools):
    """
    Adds HTTP proxy to the staging gateway

    - We need to add rhsso url to NO_PROXY, because each HTTP request from apicast will go through proxy
      Tinyproxy has a problem with http openshift routes
    - To not load configuration every time, we set APIcast to load configuration on boot instead
    """
    rhsso_url = urlparse(tools["no-ssl-sso"]).hostname
    superdomain = testconfig["threescale"]["superdomain"]
    proxy_endpoint = testconfig["proxy"]

    gateway_environment.update({"HTTP_PROXY": proxy_endpoint['http'],
                                "HTTPS_PROXY": proxy_endpoint['https'],
                                "NO_PROXY":
                                    f"backend-listener,system-master,system-provider,{rhsso_url},{superdomain}",
                                "APICAST_CONFIGURATION_LOADER": "boot",
                                "APICAST_CONFIGURATION_CACHE": 1000})
    return gateway_environment


# pylint: disable=too-many-arguments
@pytest.fixture(scope="module")
def service(backends_mapping, custom_service, service_proxy_settings, lifecycle_hooks, request, staging_gateway):
    """
        Creates service and adds mapping for POST method with path /
        We need to create the service here because there will be 2 services created and they cannot have the same name
    """
    service = custom_service({"name": blame(request, "svc")},
                             service_proxy_settings, backends_mapping, hooks=lifecycle_hooks)
    metric = service.metrics.list()[0]
    service.proxy.list().mapping_rules.create(rawobj.Mapping(metric, "/", "POST"))
    service.proxy.deploy()

    staging_gateway.reload()
    return service
