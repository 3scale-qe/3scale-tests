"""
Test if APIAP routing only match paths that contain whole routing path
"""

from urllib.parse import urlparse

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import
from testsuite.echoed_request import EchoedRequest

pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.8.1')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-4904"),
]


@pytest.fixture(scope="module")
def backend_bin(custom_backend, private_base_url):
    """Httpbin backend"""
    return custom_backend("backend_bin", endpoint=private_base_url("httpbin"))


@pytest.fixture(scope="module")
def backend_echo(custom_backend, private_base_url):
    """Echo-api backend"""
    return custom_backend("backend_echo", endpoint=private_base_url("echo_api"))


@pytest.fixture(scope="module")
def backends_mapping(backend_bin, backend_echo):
    """
    Create 2 separate backends:
        - path to Backend echo: "/test/bin"
        - path to Backend httpbin: "/bin"
    """
    return {"/test/bin": backend_echo, "/bin": backend_bin}


@pytest.fixture(scope="module")
def mapping_rules(service, backend_bin, backend_echo):
    """
    Backend echo:
        - Add mapping rule with path "/anything/test"
    Backend httpbin:
        - Add mapping rule with path "/anything/bin"
    """
    proxy = service.proxy.list()
    proxy.mapping_rules.list()[0].delete()

    test_metric = backend_echo.metrics.list()[0]
    bin_metric = backend_bin.metrics.list()[0]
    backend_echo.mapping_rules.create(rawobj.Mapping(test_metric, "/anything/test"))
    backend_bin.mapping_rules.create(rawobj.Mapping(bin_metric, "/anything/bin"))
    proxy.deploy()

    return proxy


@pytest.fixture(scope="module")
def api_client(api_client):
    """
    Client without retry attempts

    This testing expect 404 returns what is handled by default retry feature.
    To avoid long time execution because of retry client without retry will be
    used. Firstly a request with retry is made to ensure all is setup.
    """
    assert api_client().get("/bin/anything/bin").status_code == 200

    return api_client(disable_retry_status_list={404})


# pylint: disable=unused-argument
def test_apiap_routing_to_backend(api_client, mapping_rules, service, private_base_url):
    """
    Test if:
        - request with path "/test/bin/anything/test" have status code 200
        - request with path "/bin/anything/bin" have status code 200
        - request with path "/test/bin/anything/bin" have status code 404
        - request with path "/bin/anything/test" have status code 404
    """
    backends = service.backend_usages.list()
    assert len(backends) == 2
    request = api_client.get("/test/bin/anything/test")
    assert request.status_code == 200
    assert EchoedRequest.create(request).headers["host"] == urlparse(private_base_url("echo_api")).hostname

    request = api_client.get("/bin/anything/bin")
    assert request.status_code == 200
    assert EchoedRequest.create(request).headers["host"] == urlparse(private_base_url("httpbin")).hostname

    request = api_client.get("/test/bin/anything/bin")
    assert request.status_code == 404
    request = api_client.get("/bin/anything/test")
    assert request.status_code == 404
