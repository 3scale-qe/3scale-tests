"""
Test large data in post request when using http and https proxies
This test will cover APIAP feature

regression test for: https://issues.redhat.com/browse/THREESCALE-3863
"""
from urllib.parse import urlparse

from packaging.version import Version  # noqa # pylint: disable=unused-import
import pytest

from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.gateways.gateways import Capability
from testsuite.tests.toolbox.test_backend import random_string

pytestmark = [pytest.mark.skipif("TESTED_VERSION < Version('2.9')"),
              pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY)]


@pytest.fixture(scope="module")
def backends_mapping(custom_backend, private_base_url, protocol, lifecycle_hooks):
    """
    Create 2 separate backends:
        - path to Backend 1: "/bin"
        - path to Backend 2: "/bin2"
    """
    bin_url = urlparse(private_base_url("httpbin"))
    url = f"{protocol}://{bin_url.hostname}"
    return {"/bin": custom_backend("backend_one", endpoint=url, hooks=lifecycle_hooks),
            "/bin2": custom_backend("backend_two", endpoint=url, hooks=lifecycle_hooks)}


@pytest.mark.parametrize("num_bytes", [1000, 10000, 20000, 35000, 50000, 100000, 500000, 999999])
def test_large_data(api_client, num_bytes):
    """
        Test that a POST request with data of a given number of bytes will be successful when using an http(s) proxy
        Test checks both backends
    """
    data = random_string(num_bytes)

    # requests/urllib3 doesn't retry post(); need get() to wait until all is up
    api_client.get("/bin/get")

    response = api_client.post('/bin/post', data=data)
    assert response.status_code == 200
    assert response.json().get('data') == data

    response = api_client.post('/bin2/post', data=data)
    assert response.status_code == 200
    assert response.json().get('data') == data
