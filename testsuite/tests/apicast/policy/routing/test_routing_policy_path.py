"""
Rewrite spec/functional_specs/policies/routing/routing_by_path_spec.rb
"""

from socket import gethostbyname
from urllib.parse import urlsplit, urlunsplit

import pytest
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def backend_default(private_base_url, custom_backend):
    """
    Default backend with url from private_base_url.
    Require compatible backend to be used
    """
    return custom_backend("backend_default", endpoint=private_base_url("echo_api"))


@pytest.fixture(scope="module")
def httpbin_host(private_base_url):
    """Custom hostname to be set via policy"""

    return urlsplit(private_base_url("httpbin")).hostname


@pytest.fixture(scope="module")
def service(service, private_base_url, httpbin_host):
    """
    Set policy settings
    """
    routing_policy_op = {"operations": [{"op": "==", "value": "/anything/anything", "match": "path"}]}

    proxy = service.proxy.list()

    # let's convert URL to use IP address to have it different from Host header
    scheme, netloc, path, query, fragment = urlsplit(private_base_url("httpbin"))

    hostname = netloc
    user = None
    port = None
    if "@" in netloc:  # is like user:passwd@fqdn(:port)
        user, hostname = netloc.split("@", 1)
    if ":" in hostname:  # now is like fqdn:port
        hostname, port = hostname.split(":", 1)
    netloc = gethostbyname(hostname)
    if user is not None:
        netloc = f"{user}@{netloc}"
    if port is not None:
        netloc = f"{netloc}:{port}"
    url = urlunsplit((scheme, netloc, path, query, fragment))

    proxy.policies.insert(
        0,
        {
            "name": "routing",
            "version": "builtin",
            "enabled": True,
            "configuration": {"rules": [{"url": url, "host_header": httpbin_host, "condition": routing_policy_op}]},
        },
    )

    return service


def test_routing_policy_path_anything(api_client, httpbin_host):
    """
    Test for the request path send to /anything to httpbin.org/anything
    """
    response = api_client().get("/anything/anything")
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.headers["Host"] == httpbin_host


def test_routing_policy_path_alpha(api_client):
    """
    Test for the request path send to /alpha to echo api
    """
    response = api_client().get("/alpha")

    assert response.status_code == 200
    echoed_request = EchoedRequest.create(response)
    assert echoed_request.path == "/alpha"


def test_routing_policy_path(api_client):
    """
    Test for the request path send to / to echo api
    """
    response = api_client().get("/")

    assert response.status_code == 200
    echoed_request = EchoedRequest.create(response)
    assert echoed_request.path == "/"
