"""Checks that adapter can use updated values for limits with caching enabled"""
import time

import pytest

from testsuite import rawobj
from testsuite.capabilities import Capability

pytestmark = pytest.mark.required_capabilities(Capability.SERVICE_MESH)


@pytest.fixture(scope="module")
def limit(application):
    """Add and map rate limited metric to application plan."""

    service = application.service
    metric = service.metrics.create(rawobj.Metric("limit_exceeded"))

    proxy = service.proxy.list()
    proxy.mapping_rules.create(rawobj.Mapping(metric, pattern="/anything/exceeded"))

    limit = service.app_plans.list()[0].limits(metric).create({
        "metric_id": metric["id"], "period": "minute", "value": 1})

    proxy.deploy()

    return limit


def test_limit_change(limit, api_client):
    """
    Test limit change with caching enabled

    * Set up a limit
    * Exceed that limit
    * Change value of that limit
    * Wait until next period
    * Adapter should use the new limit value
    """
    client = api_client()
    assert client.get("/anything/exceeded").status_code == 200
    # Apicast allows more request to pass than is the actual limit, other gateway do not
    client.get("/anything/exceeded")
    assert client.get("/anything/exceeded").status_code == 429

    limit.update(params={"value": 5})

    time.sleep(120)

    for _ in range(5):
        assert client.get("/anything/exceeded").status_code == 200

    assert client.get("/anything/exceeded").status_code == 429
