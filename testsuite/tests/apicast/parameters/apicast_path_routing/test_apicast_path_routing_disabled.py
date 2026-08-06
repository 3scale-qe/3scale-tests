"""Rewrite of spec/openshift_specs/path_based_routing_two_backends_routing_disabed_spec.rb

Test apicast with path routing disabled.
"""

from urllib.parse import urlparse

import pytest

from testsuite.capabilities import Capability
from testsuite.echoed_request import EchoedRequest

pytestmark = pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT)


@pytest.fixture(scope="module")
def gateway_environment(gateway_environment):
    """Disabled path routing on gateway"""
    gateway_environment.update({"APICAST_PATH_ROUTING": False})
    return gateway_environment


def test_get_route_request_returns_ok(client, private_base_url):
    """Call to mapping /get should returns 200 OK."""
    response = client.get("/get")
    assert response.status_code == 200

    echoed = EchoedRequest.create(response)
    assert echoed.headers["Host"] == urlparse(private_base_url()).hostname


def test_not_matched_route_request_returns_not_found(api_client, application2):
    """Call to not matched mapping /echo returns 404 OK.

    As both services, 1 and 2, have the same public base url, however, path routing is disabled,
    request against service number 2 will fail because first service to match will be service number 1.
    Service 1 has no mapping rule /echo mapped into it.
    """
    client = api_client(application2, disable_retry_status_list={404})

    assert client.get("/echo").status_code == 404
