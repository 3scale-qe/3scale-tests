"""
Create a service with a non existent policy in the chain
and tests that on failed policy returns the correct error code.
"""
import backoff
import pytest

from testsuite import rawobj
from testsuite.capabilities import Capability

pytestmark = [pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY),
              pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6705")]


@pytest.fixture
def failing_chain(on_failed_policy) -> tuple:
    """returns a policy chain that fails the execution
       made by a non-existent policy and on_failed policy"""
    return (rawobj.PolicyConfig("invalid_policy", {}), on_failed_policy)


@pytest.fixture
def successful_chain(on_failed_policy) -> dict:
    """returns a chain that executes successfully"""
    return on_failed_policy


@pytest.fixture(params=["successful_chain", "failing_chain"])
def chain_name(request) -> str:
    """Returns if the current testing attempt is a successful or a failing one"""
    return request.param


@pytest.fixture
def policy_settings(request, chain_name):
    """
    on_failed_configuration is requested but not used to trigger
    the test cases list.
    returns the policy chain for the current run
    """
    return request.getfixturevalue(chain_name)


@pytest.fixture
def status_code(chain_name, on_failed_configuration) -> int:
    """returns the status code to be matched based on the current run"""
    if chain_name == "successful_chain":
        return 200
    return on_failed_configuration.get("error_status_code", 503)


@backoff.on_predicate(backoff.fibo,
                      lambda response: response.headers.get("server") != "openresty",
                      8, jitter=None)
def make_request(api_client):
    """Make request to the product and retry if the response isn't from APIcast """
    return api_client.get("/")


def test_on_failed_policy(application, status_code):
    """
    Sends request to apicast and check that the returned code
    is the expected one as per `status_code`
    """
    api_client = application.api_client(disable_retry_status_list=(503,))

    response = make_request(api_client)
    assert response.status_code == status_code
    assert response.headers["server"] == "openresty"
