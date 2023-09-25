"""
Test large data in post request when using http and https proxies
"""

from urllib.parse import urlparse

from packaging.version import Version  # noqa # pylint: disable=unused-import
import pytest

from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.echoed_request import EchoedRequest
from testsuite.capabilities import Capability
from testsuite.utils import random_string

pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.9')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-3863"),
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT),
]


@pytest.fixture(scope="module")
def backend_default(private_base_url, custom_backend, protocol):
    """
    Default backend with url from private_base_url.
    Url for service that is configured with http version of httpbin_go.
    """
    url = urlparse(private_base_url("httpbin_go"))
    return custom_backend("backend_default", endpoint=f"{protocol}://{url.hostname}")


@pytest.mark.parametrize("num_bytes", [1000, 10000, 20000, 35000, 50000, 100000, 500000, 999999])
def test_large_data(api_client, num_bytes):
    """Test that a POST request with data of a given number of bytes will be successful when using an http(s) proxy"""
    data = random_string(num_bytes)
    client = api_client()

    # requests/urllib3 doesn't retry post(); need get() to wait until all is up
    client.get("/get")

    response = client.post("/post", data=data)
    assert response.status_code == 200
    echo = EchoedRequest.create(response)
    assert echo.headers.get("X-Forwarded-By", "MISSING").startswith("MockServer")
    assert echo.body == data
