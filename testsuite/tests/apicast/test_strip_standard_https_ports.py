"""
When APIcast sends a request to a standard port, it should strip the port from the 'host' header.
"""
import pytest

from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.echoed_request import EchoedRequest
from testsuite.utils import blame, warn_and_skip

pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.11')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-2235")]


@pytest.fixture(scope="module", autouse=True)
def skip_saas(testconfig):
    """Gateway logs missing on SaaS"""
    if testconfig["threescale"]["deployment_type"] == "saas":
        warn_and_skip("Gateway logs missing on SaaS")


@pytest.fixture(scope="module", params=["mockserver+svc:1080",
                                        "httpbin",
                                        "httpbin_nossl"])
def private_base_url_and_expected_port(private_base_url, request):
    """
    Returns the upstream api url to be used, along with the port that is
    expected
    """
    url = private_base_url(request.param)
    port = url.split(":")[2].replace('/', '')
    return url, port if port not in {'80', '443'} else None


@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url_and_expected_port):
    """
    Sets the backend api url based on the parameter from the
    private_base_url_and_expected_port
    """
    return rawobj.Proxy(private_base_url_and_expected_port[0])


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def service_settings(request, private_base_url_and_expected_port):
    """
    Creates new random service name with each parameterization of
    private_base_url_and_expected_port
    """
    return {"name": blame(request, "svc")}


def test_strip_ports(api_client, private_base_url_and_expected_port):
    """
    Sends a request on an APIcast configured to use a particular backend.
    Asserts that:
        - if the upstream url port is a standard one (80, 443), it is stripped
         from the 'host' header of the request to the upstream api
        - otherwise is the port still present
    """
    client = api_client()
    response = client.get("/get")

    echoed_request = EchoedRequest.create(response)

    url_split = echoed_request.headers['host'].split(":")

    expected_port = private_base_url_and_expected_port[1]

    if expected_port:
        assert len(url_split) == 2
        assert url_split[1] == expected_port
    else:
        assert len(url_split) == 1
