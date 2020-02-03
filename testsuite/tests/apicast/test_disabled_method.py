"""Test that disabled method is not accessible

https://issues.jboss.org/browse/THREESCALE-3330"""


import pytest
from testsuite import rawobj


@pytest.fixture(scope="module")
def application(application):
    """disabled_method mapped to /anything/disabled_method exists and it is disabled in application plan"""

    service = application.service
    metric = service.metrics.list()[0]
    method = metric.methods.create(rawobj.Method("disabled_method"))

    proxy = service.proxy.list()
    proxy.mapping_rules.create(rawobj.Mapping(method, pattern="/anything/disabled_method"))

    service.app_plans.list()[0].limits(method).create({
        "metric_id": method["id"], "period": "eternity", "value": 0})

    proxy.update()

    return application


def test_disabled_method(api_client):
    """Call to /anything/disabled_method is forbidden and returns appropriate code 403"""

    response = api_client.get("/anything/disabled_method")
    assert response.status_code == 403


def test_anything_else_is_accessible(api_client):
    """Call to /anthing/else works without problem, status code is 200"""

    assert api_client.get("/anything/else").status_code == 200
