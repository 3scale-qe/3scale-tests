"""
When the logging policy is configured to show logs only on a responses with
particular status code, only those responses are logged.
"""

import pytest

from testsuite import rawobj
from testsuite.capabilities import Capability
from testsuite.utils import randomize

pytestmark = pytest.mark.required_capabilities(Capability.LOGS)

LOG_MESSAGE = randomize("custom_and_unique_access_log")


@pytest.fixture(scope="module")
def policy_settings():
    """
    Customize the access logs format and sets the logging condition to log
    only 200 responses
    """
    return rawobj.PolicyConfig(
        "logging",
        {
            "condition": {
                "operations": [{"op": "==", "match": "{{status}}", "match_type": "liquid", "value": "200"}],
                "combine_op": "and",
            },
            "custom_logging": LOG_MESSAGE,
        },
    )


@pytest.mark.nopersistence  # Test checks changes during test run hence is incompatible with persistence plugin
def test_logging(api_client, staging_gateway):
    """
    Tests that the logs contain the log only after a 200 response
    """
    client = api_client()

    client.get("/status/201")
    logs = staging_gateway.get_logs()
    assert LOG_MESSAGE not in logs

    client.get("/status/200")
    logs = staging_gateway.get_logs()
    assert LOG_MESSAGE in logs
