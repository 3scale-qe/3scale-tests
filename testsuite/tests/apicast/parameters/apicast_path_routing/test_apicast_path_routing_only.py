"""Rewrite of spec/openshift_specs/path_based_routing_only_spec.rb

When `APICAST_PATH_ROUTING_ONLY` parameter is set to true, the gateway uses path-based routing
and will not fallback to the default host-based routing.
The API request will be routed to the first service that has a matching mapping rule,
from the list of services for which the value of the Host header of the request matches the Public Base URL.
"""

from urllib.parse import urlparse

import pytest

from testsuite.capabilities import Capability
from testsuite.echoed_request import EchoedRequest
from testsuite.gateways.apicast.template import TemplateApicast

pytestmark = pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT)


@pytest.fixture(scope="module")
def gateway_kind():
    """Gateway class to use for tests"""
    return TemplateApicast


@pytest.fixture(scope="module")
def gateway_environment(gateway_environment):
    """Sets gateway to use only path routing"""
    gateway_environment.update({"APICAST_PATH_ROUTING_ONLY": 1})
    return gateway_environment


def test_get_route_request_returns_ok(client, private_base_url):
    """Call to mapping /get returns 200 OK."""
    response = client.get("/get")
    assert response.status_code == 200

    echoed = EchoedRequest.create(response)
    assert echoed.headers["Host"] == urlparse(private_base_url()).hostname


def test_echo_route_request_returns_ok(client2, private_base_url):
    """Call to mapping /echo returns 200 OK."""
    response = client2.get("/echo")
    assert response.status_code == 200

    echoed = EchoedRequest.create(response)
    assert echoed.headers["Host"] == urlparse(private_base_url("echo_api")).hostname


def test_not_mapped_route_returns_not_found(application, api_client):
    """Call to mapping /anything/not-today returns 404 NotFound.

    Path-based routing fails and it will not fallback to the default host-based routing.
    """

    # wait until all is ready (retry on 503/404)
    application.test_request()

    client = api_client(disable_retry_status_list={404})

    assert client.get("/anything/not-today").status_code == 404
