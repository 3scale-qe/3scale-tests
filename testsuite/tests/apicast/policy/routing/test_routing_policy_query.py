"""
Rewrite spec/functional_specs/policies/routing/routing_by_query_spec.rb
"""

from urllib.parse import urlparse

import pytest

from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def service(service, private_base_url):
    """
    Set policy settings
    """
    test_query1 = {"operations": [{"op": "==", "value": "route1", "match": "query_arg", "query_arg_name": "test_arg"}]}
    test_query2 = {"operations": [{"op": "==", "value": "route2", "match": "query_arg", "query_arg_name": "test_arg"}]}
    proxy = service.proxy.list()
    proxy.policies.insert(
        0,
        {
            "name": "routing",
            "version": "builtin",
            "enabled": True,
            "configuration": {
                "rules": [
                    {"url": private_base_url("echo_api") + "/route1", "condition": test_query1},
                    {"url": private_base_url("echo_api") + "/route2", "condition": test_query2},
                ]
            },
        },
    )

    return service


@pytest.mark.smoke
def test_routing_policy_route1(api_client, private_base_url):
    """
    Test for the request with matching path to /route1/get
    """
    parsed_url = urlparse(private_base_url("echo_api"))
    response = api_client().get("/get", params={"test_arg": "route1"})
    assert response.status_code == 200
    echoed_request = EchoedRequest.create(response)

    assert echoed_request.headers["Host"] == parsed_url.hostname
    assert echoed_request.path == "/route1/get"


def test_routing_policy_route2(api_client, private_base_url):
    """
    Test for the request with matching path to /route2/get
    """
    parsed_url = urlparse(private_base_url("echo_api"))
    response = api_client().get("/get", params={"test_arg": "route2"})
    assert response.status_code == 200
    echoed_request = EchoedRequest.create(response)

    assert echoed_request.headers["Host"] == parsed_url.hostname
    assert echoed_request.path == "/route2/get"


def test_routing_policy_noroute(api_client, private_base_url):
    """
    Test for the request without matching value to echo api
    """
    parsed_url = urlparse(private_base_url())
    response = api_client().get("/get", params={"test_arg": "noroute"})
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.headers["Host"] == parsed_url.hostname


def test_routing_policy_empty(api_client, private_base_url):
    """
    Test for the request without params and matching value to echo api
    """
    parsed_url = urlparse(private_base_url())
    response = api_client().get("/get")
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.headers["Host"] == parsed_url.hostname
