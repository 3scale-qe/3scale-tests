"""
When the logging policy is set to disable logging, than no access logs are created
"""
import pytest
from testsuite import rawobj
from testsuite.utils import randomize


@pytest.fixture(scope="module")
def policy_settings():
    """
    Sets the logging policy to disable logging
    """
    return rawobj.PolicyConfig("logging", {
        "enable_access_logs": False
    })


def test_logging(api_client, staging_gateway):
    """
    Asserts that the access log containing the randomized endpoint is not in the apicast logs
    """
    endpoint = randomize("/anything/endpoint")
    api_client.get(endpoint)

    logs = staging_gateway.get_logs()
    logs = logs.splitlines()

    contains_log = False
    for line in logs:
        contains_log = contains_log or ((endpoint in line) and "lua" not in line)

    assert not contains_log
