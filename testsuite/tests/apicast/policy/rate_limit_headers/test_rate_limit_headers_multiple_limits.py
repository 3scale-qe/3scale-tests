"""
Tests that when an app plan has two limits with different time frame, the RateLimit information for
the currently more constrained limit are sent.
"""

from packaging.version import Version  # noqa # pylint: disable=unused-import
import pytest
from testsuite.utils import blame, wait_interval, wait_until_next_minute, wait_interval_hour
from testsuite import rawobj
from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import

# rate-limit have been always unstable, likely because of overhead in staging apicast?
pytestmark = [
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-3795"),
    pytest.mark.skipif("TESTED_VERSION < Version('2.9')"),
    pytest.mark.flaky,
]


@pytest.fixture(scope="module")
def app_plan(service, custom_app_plan, request):
    """
    Creates an app plan with two limits, one with a minute and one with an hour scope,
    both on the default 'Hits' metric
    """
    metric = service.metrics.list()[0]

    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "app")), service)
    plan.limits(metric).create({"metric_id": metric["id"], "period": "minute", "value": 5})
    plan.limits(metric).create({"metric_id": metric["id"], "period": "hour", "value": 7})
    return plan


@pytest.mark.nopersistence  # Test checks changes during test run hence is incompatible with persistence plugin
def test_multiple_limits(api_client):
    """
    - sends five requests
    - asserts that the RateLimits are correctly reported
    - waits until the 'minute' limits are refreshed, the 'hour' limit is now the more constrained one
    - sends a request
    - asserts, that the RateLimits for the 'hour' limit are returned
    """
    client = api_client()

    wait_interval()
    # prevents refreshing the hour limits in the middle of the test, and asserts the reamining seconds in the
    # hour limit will be greater then 60
    wait_interval_hour(max_min=57)

    for i in range(5):
        response = client.get("/anything")
        assert response.status_code == 200
        assert int(response.headers["RateLimit-Limit"]) == 5, (
            f"The response rate limits failed on the {i} call"
            f"\nRateLimit-Remaining: "
            f"{response.headers['RateLimit-Remaining']}"
        )
        assert int(response.headers["RateLimit-Remaining"]) == 5 - i - 1

    wait_until_next_minute()

    response = client.get("/anything")
    assert int(response.headers["RateLimit-Limit"]) == 7
    assert int(response.headers["RateLimit-Remaining"]) == 1
    assert int(response.headers["RateLimit-Reset"]) > 60
