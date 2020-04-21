"""Rewrite of spec/openshift_specs/path_based_routing_two_backends_routing_disabed_spec.rb

Test apicast with path routing disabled.
"""
from urllib.parse import urlparse

import pytest
import requests

from testsuite.echoed_request import EchoedRequest
from testsuite.gateways.gateways import Capability

pytestmark = pytest.mark.required_capabilities(Capability.APICAST)


def test_get_route_request_returns_ok(api_client, private_base_url):
    """Call to mapping /get should returns 200 OK."""
    response = api_client.get("/get")
    echoed = EchoedRequest.create(response)

    assert response.status_code == 200
    assert echoed.headers["Host"] == urlparse(private_base_url()).hostname


def test_not_matched_route_request_returns_not_found(application):
    """Call to not matched mapping /anything/blah returns 404 OK."""
    session = requests.Session()
    session.auth = application.authobj

    # skip retrying on 404 by passing Session instance to it
    client = application.api_client(session=session)

    assert client.get("/anything/blah").status_code == 404
