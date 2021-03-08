"""
When the logging policy is configured to show logs in a json format,
the logs are shown that way
"""
import pytest
from testsuite import rawobj
from testsuite.capabilities import Capability
from testsuite.utils import randomize

pytestmark = pytest.mark.required_capabilities(Capability.LOGS)

VALUE = randomize("custom_and_unique_value")
JSON_OBJECT_CONFIG = [{
    "key": "key",
    "value": VALUE,
    "value_type": "plain"}]
JSON = "{\"key\":\"" + VALUE + "\"}"


@pytest.fixture(scope="module")
def policy_settings():
    """Customize the access logs json format"""
    return rawobj.PolicyConfig("logging", {
        "enable_access_logs": False,
        "enable_json_logs": True,
        "json_object_config": JSON_OBJECT_CONFIG
        })


def test_logging(api_client, staging_gateway):
    """
    Tests that the logs contain the log in the json format
    """
    api_client().get("/anything")
    logs = staging_gateway.get_logs()
    assert JSON in logs
