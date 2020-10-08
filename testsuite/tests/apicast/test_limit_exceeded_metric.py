"""
Test that limit exceeded metric returns status 429
"""


import pytest
from testsuite import rawobj

pytestmark = [
    pytest.mark.required_capabilities(),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-2752")]


@pytest.fixture(scope="module")
def application(application):
    """Add and map rate limited metric to application plan."""

    service = application.service
    metric = service.metrics.create(rawobj.Metric("limit_exceeded"))

    proxy = service.proxy.list()
    proxy.mapping_rules.create(rawobj.Mapping(metric, pattern="/anything/exceeded"))

    service.app_plans.list()[0].limits(metric).create({
        "metric_id": metric["id"], "period": "day", "value": 1})

    proxy.update()

    return application


def test_limit_exceeded(api_client):
    """Call to /anything/exceeded should returns 429 Too Many Requests."""

    assert api_client.get("/anything/exceeded").status_code == 200
    # Apicast allows more request to pass than is the actual limit, other gateway do not
    api_client.get("/anything/exceeded")
    assert api_client.get("/anything/exceeded").status_code == 429


def test_anything_else_is_ok(api_client):
    """Call to /anything/else should returns 200 OK."""

    assert api_client.get("/anything/else").status_code == 200
