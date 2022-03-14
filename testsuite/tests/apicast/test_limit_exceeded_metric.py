"""
Test that limit exceeded metric returns status 429 or 403 if using WASMGateway
"""


import pytest
from testsuite import rawobj
from testsuite.gateways.wasm import WASMGateway

pytestmark = [
    pytest.mark.nopersistence,
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

    proxy.deploy()

    return application


@pytest.fixture(scope="session")
def error_status_code_too_many(staging_gateway):
    """'Too many requests' status codes
        are different when using WASMGateway"""
    if isinstance(staging_gateway, WASMGateway):
        return 403
    return 429


def test_limit_exceeded(api_client, error_status_code_too_many):
    """Call to /anything/exceeded should returns 429 Too Many Requests."""
    client = api_client()

    assert client.get("/anything/exceeded").status_code == 200
    # Apicast allows more request to pass than is the actual limit, other gateway do not
    client.get("/anything/exceeded")
    assert client.get("/anything/exceeded").status_code == error_status_code_too_many


def test_anything_else_is_ok(api_client):
    """Call to /anything/else should returns 200 OK."""

    assert api_client().get("/anything/else").status_code == 200
