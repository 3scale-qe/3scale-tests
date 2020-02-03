"""Test that URL with escape sequence(s) is processed correctly
and relevant mapping/metric is applied

https://issues.jboss.org/browse/THREESCALE-3468"""


import pytest
from testsuite import rawobj


@pytest.fixture(scope="module")
def service(service):
    """Have mapping with {pattern} matching defined: /anything/foo/{bar}/baz"""

    metric = service.metrics.create(rawobj.Metric("escape_sequence"))

    proxy = service.proxy.list()
    proxy.mapping_rules.create(rawobj.Mapping(metric, pattern="/anything/foo/{bar}/baz"))
    proxy.update()

    return service


def test_mapping_with_escape_sequence(api_client, application):
    """When making request to /anything/foo/bar%20%20bar/baz
    then it should pass, metric should increase"""

    response = api_client.get("/anything/foo/bar%20%20bar/baz")
    assert response.status_code == 200

    analytics = application.threescale_client.analytics
    hits = analytics.list_by_service(application["service_id"], metric_name="escape_sequence")["total"]
    assert hits == 1
