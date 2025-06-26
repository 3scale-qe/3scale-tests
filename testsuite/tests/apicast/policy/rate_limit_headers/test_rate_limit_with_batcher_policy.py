"""
Tests that the combination with the batcher policy works as supposed
"""

import time

import pytest
from packaging.version import Version

from testsuite import TESTED_VERSION, rawobj
from testsuite.utils import blame, wait_interval

# rate-limit have been always unstable, likely because of overhead in staging apicast?
pytestmark = [
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-3795"),
    pytest.mark.skipif(TESTED_VERSION < Version("2.9"), reason="TESTED_VERSION < Version('2.9')"),
    pytest.mark.flaky,
]


@pytest.fixture(scope="module")
def policy_settings():
    """
    Enables the batcher policy
    """
    return rawobj.PolicyConfig("3scale_batcher", {"batch_report_seconds": 1})


@pytest.fixture(scope="module")
def app_plan(service, custom_app_plan, request):
    """
    Creates an app plan with a limit on hits
    """
    metric = service.metrics.list()[0]

    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "app")), service)
    plan.limits(metric).create({"metric_id": metric["id"], "period": "minute", "value": 10})
    return plan


def test_multiple_limits(api_client):
    """
    - sends a number (5) of requests
    - waits for the batcher policy to report the analytics
    - sends a request
    - asserts that the RateLimit information correspond to the numbers reported by the batcher policy
    (The reported number is -1 of the reality, as the last request was not reported), the combination with the
    batcher policy is not aimed to be 100% accurate)
    """
    client = api_client()
    wait_interval()

    for _ in range(5):
        assert client.get("/anything").status_code == 200

    # waits for the batcher policy to report
    time.sleep(2)

    response = client.get("/anything")

    assert int(response.headers["RateLimit-Limit"]) == 10
    assert int(response.headers["RateLimit-Remaining"]) == 5
    assert int(response.headers["RateLimit-Reset"]) <= 60
