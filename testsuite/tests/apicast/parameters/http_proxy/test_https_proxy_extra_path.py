"""Test that path of request to private backend is correct with https proxy"""

from urllib.parse import urlparse

from packaging.version import Version  # noqa # pylint: disable=unused-import
import pytest

from testsuite.capabilities import Capability
from testsuite.echoed_request import EchoedRequest
from testsuite import rawobj
from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import

pytestmark = [pytest.mark.required_capabilities(Capability.CUSTOM_ENVIRONMENT)]


@pytest.fixture(scope="module")
def extra_path():
    """Extra path fragment to be added to the private base-url"""
    return "/anything/else"


@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url, extra_path):
    """Set https:// private backend with extra path fragment"""
    url = urlparse(private_base_url("httpbin_go"))
    return rawobj.Proxy(f"https://{url.hostname}{extra_path}")


@pytest.fixture(scope="module")
def gateway_environment(gateway_environment, testconfig, tools, rhsso_kind):
    """
    Set apicast environment:
        - HTTPS_PROXY parameter
        - NO_PROXY - needed to skip proxy for internal services: system, backend, sso
    """
    key = "no-ssl-rhbk"
    if rhsso_kind == "rhsso":
        key = "no-ssl-sso"
    rhsso_url = urlparse(tools[key]).hostname
    https_proxy = testconfig["proxy"]["https"]

    gateway_environment.update(
        {"HTTPS_PROXY": https_proxy, "NO_PROXY": f"backend-listener,system-master,system-provider,{rhsso_url}"}
    )
    return gateway_environment


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-8426")
@pytest.mark.skipif("TESTED_VERSION <= Version('2.12')")
def test_https_proxy_extra_path(api_client, extra_path):
    """
    Given private base url including extra path fragment /anything/else
    when request to public base url with path fragment /get included
    then request to private backend has properly path set /anything/else/get
    """
    response = api_client().get("/get")
    assert response.status_code == 200
    echo = EchoedRequest.create(response)
    assert echo.headers["x-forwarded-by"].startswith("MockServer")
    assert echo.path == f"{extra_path}/get"
