"""
Rewrite spec/functional_specs/policies/routing/routing_with_multiple_conditions_and_spec.rb
"""

from urllib.parse import urlparse

import pytest

from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def service(service, private_base_url):
    """
    Set policy settings
    """
    test_header1 = {"op": "==", "value": "route", "match": "header", "header_name": "Test1"}
    test_header2 = {"op": "matches", "value": "test", "match": "header", "header_name": "Test2"}
    proxy = service.proxy.list()
    proxy.policies.insert(
        0,
        {
            "name": "routing",
            "version": "builtin",
            "enabled": True,
            "configuration": {
                "rules": [
                    {
                        "url": private_base_url("echo_api") + "/route",
                        "condition": {"combine_op": "and", "operations": [test_header1, test_header2]},
                    }
                ]
            },
        },
    )

    return service


@pytest.mark.smoke
def test_routing_policy_route_testing(api_client, private_base_url):
    """
    Test for the request send with Test1 and Test2 to /route/get
    """
    parsed_url = urlparse(private_base_url("echo_api"))
    response = api_client().get("/get", headers={"Test1": "route", "Test2": "testing"})
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.headers["Host"] == parsed_url.hostname
    assert echoed_request.path == "/route/get"


def test_routing_policy_route_hello(api_client, private_base_url):
    """
    Test for the request send with Test1 and Test2 to /route/get
    """
    parsed_url = urlparse(private_base_url())
    response = api_client().get("/get", headers={"Test1": "route", "Test2": "hello"})
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.headers["Host"] == parsed_url.hostname


def test_routing_policy_noroute_test(api_client, private_base_url):
    """
    Test for the request send with Test1 valid and Test2 invalid value to httpbin api
    """
    parsed_url = urlparse(private_base_url())
    response = api_client().get("/get", headers={"Test1": "noroute", "Test2": "test"})
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.headers["Host"] == parsed_url.hostname


def test_routing_policy_route(api_client, private_base_url):
    """
    Test for the request send without Test2 to httpbin api
    """
    parsed_url = urlparse(private_base_url())
    response = api_client().get("/get", headers={"Test1": "route"})
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.headers["Host"] == parsed_url.hostname


def test_routing_policy_empty(api_client, private_base_url):
    """
    Test for the request send without any header to / to httpbin api
    """
    parsed_url = urlparse(private_base_url())
    response = api_client().get("/get")
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.headers["Host"] == parsed_url.hostname
