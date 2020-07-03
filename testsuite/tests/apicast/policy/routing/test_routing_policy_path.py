"""
Rewrite spec/functional_specs/policies/routing/routing_by_path_spec.rb
"""

from urllib.parse import urlparse
import pytest
from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url):
    """
    Require compatible backend to be used
    """
    return rawobj.Proxy(private_base_url("echo_api"))


@pytest.fixture(scope="module")
def test_httpbin_host(private_base_url):
    """Custom hostname to be set via policy"""

    return "test.%s" % urlparse(private_base_url("httpbin")).hostname


@pytest.fixture(scope="module")
def service(service, private_base_url, test_httpbin_host):
    """
    Set policy settings
    """
    routing_policy_op = {"operations": [
        {"op": "==", "value": "/anything", "match": "path"}]}

    proxy = service.proxy.list()
    proxy.policies.insert(0, {
        "name": "routing",
        "version": "builtin",
        "enabled": True,
        "configuration": {
            "rules": [{"url": private_base_url("httpbin"),
                       "host_header": test_httpbin_host,
                       "condition": routing_policy_op}]}})

    return service


@pytest.mark.smoke
def test_routing_policy_path_anything(api_client, test_httpbin_host):
    """
    Test for the request path send to /anything to httpbin.org/anything
    """
    response = api_client.get("/anything")
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.headers["Host"] == test_httpbin_host


def test_routing_policy_path_alpha(api_client):
    """
    Test for the request path send to /alpha to echo api
    """
    response = api_client.get("/alpha")

    assert response.status_code == 200
    echoed_request = EchoedRequest.create(response)
    assert echoed_request.path == "/alpha"


def test_routing_policy_path(api_client):
    """
    Test for the request path send to / to echo api
    """
    response = api_client.get("/")
    echoed_request = EchoedRequest.create(response)

    assert response.status_code == 200
    assert echoed_request.path == "/"
