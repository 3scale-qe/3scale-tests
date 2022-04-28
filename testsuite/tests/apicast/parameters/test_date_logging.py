"""
Test for logging policy with custom date format
"""
from datetime import datetime, timezone

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import rawobj, TESTED_VERSION, APICAST_OPERATOR_VERSION  # noqa # pylint: disable=unused-import
from testsuite.capabilities import Capability

pytestmark = [
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6594"),
    pytest.mark.required_capabilities(Capability.LOGS),
    pytest.mark.skipif("TESTED_VERSION < Version('2.12')"),
    pytest.mark.skipif("APICAST_OPERATOR_VERSION < Version('0.6.0')")
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
