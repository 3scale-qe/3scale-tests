"""
When the logging policy is configured to show logs in a custom format,
they are shown that way
"""
import pytest
from testsuite import rawobj
from testsuite.capabilities import Capability
from testsuite.utils import randomize

pytestmark = pytest.mark.required_capabilities(Capability.LOGS)


LOG_MESSAGE = randomize("custom_and_unique_access_log")


@pytest.fixture(scope="module")
def policy_settings():
    """Customize the access logs format"""
    return rawobj.PolicyConfig("logging", {
        "condition": {
            "combine_op": "and"},
        "custom_logging": LOG_MESSAGE
        })


def test_logging(api_client, staging_gateway):
    """
    Tests that the logs contain the log in the customized format
    """
    api_client().get("/anything")
    logs = staging_gateway.get_logs()
    assert LOG_MESSAGE in logs
