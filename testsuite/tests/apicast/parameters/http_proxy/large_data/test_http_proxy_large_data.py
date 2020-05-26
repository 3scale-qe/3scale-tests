"""
Test large data in post request when using http and https proxies

regression test for: https://issues.redhat.com/browse/THREESCALE-3863
"""
from urllib.parse import urlparse

from packaging.version import Version  # noqa # pylint: disable=unused-import
import pytest

from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.gateways.gateways import Capability
from testsuite.utils import random_string

pytestmark = [pytest.mark.skipif("TESTED_VERSION < Version('2.9')"),
              pytest.mark.required_capabilities(Capability.APICAST, Capability.CUSTOM_ENVIRONMENT)]


@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url, protocol):
    """Url for service that is configured with http version of echo api"""
    url = urlparse(private_base_url("httpbin"))
    return rawobj.Proxy(f"{protocol}://{url.hostname}")


@pytest.mark.parametrize("num_bytes", [1000, 10000, 20000, 35000, 50000, 100000, 500000, 999999])
def test_large_data(api_client, num_bytes):
    """Test that a POST request with data of a given number of bytes will be successful when using an http(s) proxy"""
    data = random_string(num_bytes)

    response = api_client.post('/post', data=data)
    assert response.status_code == 200
    assert response.json().get('data') == data
