"""
Test for logging policy with liquid split
"""

import pytest

from testsuite import rawobj
from testsuite.capabilities import Capability

pytestmark = [
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7643"),
    pytest.mark.required_capabilities(Capability.LOGS),
]


@pytest.fixture(scope="module")
def policy_settings():
    """Customize the access logs format"""
    return rawobj.PolicyConfig("logging", {"custom_logging": '{% assign s = "1,2,3,4,5" | split: "," | json %}{{ s }}'})


def test_date_logging(api_client, staging_gateway):
    """
    Test that the logs contain the log in the correct format
    """
    api_client().get("/anything")
    logs = staging_gateway.get_logs()
    assert '["1","2","3","4","5"]' in logs
