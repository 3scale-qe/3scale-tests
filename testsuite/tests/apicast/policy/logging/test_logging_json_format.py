"""
When the logging policy is configured to show logs in a json format,
the logs are shown that way
"""
import pytest

from testsuite import rawobj
from testsuite.capabilities import Capability
from testsuite.utils import randomize

pytestmark = pytest.mark.required_capabilities(Capability.LOGS)


@pytest.fixture(scope="module")
def json_value():
    """Json value for logging policy"""
    return randomize("custom_and_unique_value")


@pytest.fixture(scope="module")
def policy_settings(json_value):
    """Customize the access logs json format"""
    config = [{"key": "key", "value": json_value, "value_type": "plain"}]
    return rawobj.PolicyConfig(
        "logging", {"enable_access_logs": False, "enable_json_logs": True, "json_object_config": config}
    )


def test_logging(api_client, staging_gateway, json_value):
    """
    Tests that the logs contain the log in the json format
    """
    api_client().get("/anything")
    logs = staging_gateway.get_logs()
    assert '{"key":"' + json_value + '"}' in logs
