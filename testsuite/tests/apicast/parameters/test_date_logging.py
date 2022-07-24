"""
Test for logging policy with custom date format
"""
from datetime import datetime, timezone

import pytest

from testsuite import rawobj
from testsuite.capabilities import Capability

pytestmark = [
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6594"),
    pytest.mark.required_capabilities(Capability.LOGS),
    pytest.mark.require_version("2.12"),
    pytest.mark.require_apicast_operator_version("0.6.0")
]


@pytest.fixture(scope="module")
def service(service):
    """Add policy to the first service"""
    policy = rawobj.PolicyConfig("logging", {"custom_logging": '{{ time_local | date: "%m %d, %Y" }}'})
    service.proxy.list().policies.append(policy)
    return service


def test_date_logging(api_client, staging_gateway):
    """
    Test that the logs contain the log in the correct date format
    """
    api_client().get("/anything")
    logs = staging_gateway.get_logs()
    today = datetime.now(timezone.utc).strftime("%m %d, %Y")
    assert today in logs
