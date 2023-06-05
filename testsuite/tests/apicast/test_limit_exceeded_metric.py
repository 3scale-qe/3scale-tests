"""
Test that limit exceeded metric returns status 429 or 403 if using WASMGateway
"""

import pytest

from testsuite import rawobj

pytestmark = [
    pytest.mark.nopersistence,
    pytest.mark.required_capabilities(),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-2752"),
]


@pytest.fixture(scope="module")
def application(application):
    """Add and map rate limited metric to application plan."""

    service = application.service
    metric = service.metrics.create(rawobj.Metric("limit_exceeded"))

    proxy = service.proxy.list()
    proxy.mapping_rules.create(rawobj.Mapping(metric, pattern="/anything/exceeded"))

    service.app_plans.list()[0].limits(metric).create({"metric_id": metric["id"], "period": "day", "value": 1})

    proxy.deploy()

    return application


@pytest.fixture(scope="module")
def exceed_limit(api_client):
    """
    Apicast allows more request to pass than is the actual limit, hence we need to exceed limit of /anything/exceeded
    endpoint to ensure that test will pass as expected. Extraction of this functionality to a separate fixture is due
    to the persistence plugin
    """
    assert api_client().get("/anything/exceeded").status_code == 200

    return True


@pytest.mark.usefixtures("exceed_limit")
def test_limit_exceeded(api_client):
    """Call to /anything/exceeded should return 429 Too Many Requests."""
    client = api_client()
    client.get("/anything/exceeded")
    assert client.get("/anything/exceeded").status_code == 429


def test_anything_else_is_ok(api_client):
    """Call to /anything/else should return 200 OK."""

    assert api_client().get("/anything/else").status_code == 200

