"""Rewrite of spec/openshift_specs/path_based_routing_only_spec.rb

When `APICAST_PATH_ROUTING_ONLY` parameter is set to true, the gateway uses path-based routing
and will not fallback to the default host-based routing.
The API request will be routed to the first service that has a matching mapping rule,
from the list of services for which the value of the Host header of the request matches the Public Base URL.
"""
from urllib.parse import urlparse

import pytest
import requests

from testsuite.echoed_request import EchoedRequest
from testsuite.gateways.gateways import Capability

pytestmark = pytest.mark.required_capabilities(Capability.APICAST, Capability.CUSTOM_ENVIRONMENT)


@pytest.fixture(scope="module")
def gateway_environment(gateway_environment):
    """Sets gateway to use only path routing"""
    gateway_environment.update({"APICAST_PATH_ROUTING_ONLY": 1})
    return gateway_environment


def test_get_route_request_returns_ok(api_client, private_base_url):
    """Call to mapping /get returns 200 OK."""
    response = api_client.get("/get")
    echoed = EchoedRequest.create(response)

    assert response.status_code == 200
    assert echoed.headers["Host"] == urlparse(private_base_url()).hostname


def test_echo_route_request_returns_ok(api_client2, private_base_url):
    """Call to mapping /echo returns 200 OK."""
    response = api_client2.get("/echo")
    echoed = EchoedRequest.create(response)

    assert response.status_code == 200
    assert echoed.headers["Host"] == urlparse(private_base_url("echo_api")).hostname


def test_not_mapped_route_returns_not_found(application):
    """Call to mapping /anything/not-today returns 404 NotFound.

    Path-based routing fails and it will not fallback to the default host-based routing.
    """
    session = requests.Session()
    session.auth = application.authobj

    # skip retrying on 404 by passing Session instance to it
    client = application.api_client(session=session)

    assert client.get("/anything/not-today").status_code == 404
