"""Rewrite of spec/openshift_specs/path_based_routing_two_backends_spec.rb

When `APICAST_PATH_ROUTING` parameter is set to true, the gateway will use path-based routing
in addition to the default host-based routing.
The API request will be routed to the first service that has a matching mapping rule,
from the list of services for which the value of the Host header of the request matches the Public Base URL.
"""

from urllib.parse import urlparse

import pytest

from testsuite.capabilities import Capability
from testsuite.echoed_request import EchoedRequest

pytestmark = pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT)


@pytest.fixture(scope="module")
def gateway_environment(gateway_environment):
    """Enables path routing on gateway"""
    gateway_environment.update({"APICAST_PATH_ROUTING": True})
    return gateway_environment


def test_get_route_request_returns_ok(client, private_base_url):
    """Call to mapping /get returns 200 OK."""
    response = client.get("/get")
    echoed = EchoedRequest.create(response)

    assert response.status_code == 200
    assert echoed.headers["Host"] == urlparse(private_base_url()).hostname


def test_echo_route_request_returns_ok(client2, private_base_url):
    """Call to mapping /echo returns 200 OK."""
    response = client2.get("/echo")
    assert response.status_code == 200

    echoed = EchoedRequest.create(response)
    assert echoed.headers["Host"] == urlparse(private_base_url("echo_api")).hostname


def test_not_mapped_route_returns_not_found(application2, api_client):
    """Call to not mapped route /anything/blah returns 404 Not Found.

    Path-based routing fails and it fallback to the default host-based routing.
    """
    client = api_client(application2, disable_retry_status_list={404})

    assert client.get("/anything/blah").status_code == 404
