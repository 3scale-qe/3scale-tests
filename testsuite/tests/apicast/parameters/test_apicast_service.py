"""
https://issues.redhat.com/browse/THREESCALE-1524
Test for env variable APICAST_SERVICES_FILTER_BY_URL
"""
import pytest
import requests

from testsuite.gateways.gateways import Capability

pytestmark = pytest.mark.required_capabilities(Capability.APICAST, Capability.CUSTOM_ENVIRONMENT)


@pytest.fixture(scope="module")
def backends_mapping(custom_backend, private_base_url):
    """
    Create custom backend with endpoint httpbin and second one with endpoint echo_api
    """
    return {
        "/bin": custom_backend("bin", endpoint=private_base_url("httpbin")),
        "/echo": custom_backend("echo", endpoint=private_base_url("echo_api"))}


@pytest.fixture(scope="module")
def api_client(application):
    """
    Sets session to api client for skipping retrying feature.
    """

    session = requests.Session()
    session.auth = application.authobj
    return application.api_client(session=session)


@pytest.fixture(scope="module")
def gateway_environment(gateway_environment):
    """
    Set env variable 'APICAST_SERVICES_FILTER_BY_URL' to regex that takes any httpbin url
    """
    gateway_environment.update({"APICAST_SERVICES_FILTER_BY_URL": ".*httpbin.*"})
    return gateway_environment


@pytest.mark.xfail
# https://issues.redhat.com/browse/THREESCALE-5241
def test_filter_by_url(api_client):
    """
    Request to 'bin' backend should return 200
    Request to 'echo' backend should return 404
    """
    request = api_client.get("/bin")
    assert request.status_code == 200
    request = api_client.get("/echo")
    assert request.status_code == 404
