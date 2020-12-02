"""
When the logging policy is set to enable logging, the logs are outputed as usual
"""
import pytest
from testsuite import rawobj
from testsuite.gateways.gateways import Capability
from testsuite.utils import randomize

pytestmark = pytest.mark.required_capabilities(Capability.LOGS)


@pytest.fixture(scope="module")
def policy_settings():
    """
    Sets the logging policy to enable logging
    """
    return rawobj.PolicyConfig("logging", {
        "enable_access_logs": True
    })


def test_logging(api_client, staging_gateway):
    """
    Asserts that the access log containing the randomized endpoint is in the apicast logs
    """
    endpoint = randomize("/anything/endpoint")
    api_client.get(endpoint)

    logs = staging_gateway.get_logs()
    logs = logs.splitlines()

    contains_log = False
    for line in logs:
        contains_log = contains_log or ((endpoint in line) and "lua" not in line)

    assert contains_log
