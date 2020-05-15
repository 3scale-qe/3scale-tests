"""
Rewrite:  spec/functional_specs/mapping_rules_matching_order_spec.rb

When api is using mapping rules with matching order, request will hit
endpoint and increase the metric twice (once for each mapping).
When last flag is enabled on the first rule, the metric will be increased
only once.
"""

import pytest
from testsuite import rawobj

pytestmark = pytest.mark.required_capabilities()


@pytest.fixture(scope="module")
def service(service):
    """
    Create four mapping rules.
    The first should be a prefix of the second.
    The third should be a prefix of the fourth one and it should have the
    'last' flag set to 'true'

    The first and second should use one metric, the third and fourth should
    also use the same metric, but different from the first one
    """

    proxy = service.proxy.list()

    metric_twice = service.metrics.create(rawobj.Metric("metric_twice"))
    metric_once = service.metrics.create(rawobj.Metric("metric_once"))

    create_mapping_rule(proxy, metric_twice, pattern="/anything/foo/")
    create_mapping_rule(proxy, metric_twice, pattern="/anything/foo/123")
    create_mapping_rule(proxy, metric_once, pattern="/anything/bar/", last="true")
    create_mapping_rule(proxy, metric_once, pattern="/anything/bar/123")

    proxy.update()

    return service


def create_mapping_rule(proxy, metric: dict, pattern: str, last: str = "false"):
    """Creates a mapping rule"""
    proxy.mapping_rules.create(
        rawobj.Mapping(metric, pattern=pattern, http_method="GET", last=last))


def test_mapping_rules_matching_order(api_client, application):
    """
    Send a request matching the second mapping rule.
    Assert that the request was matched by both first and second mapping and
    the metric increased twice.

    Send a request matching the fourth mapping rule.
    Assert that after matching the third one with the last flag set to true,
    no other mapping has been matched, therefor the hits increased only once.
    """

    response_twice = api_client.get("/anything/foo/123")
    assert response_twice.status_code == 200

    analytics = application.threescale_client.analytics
    metric_twice = analytics.list_by_service(application["service_id"],
                                             metric_name="metric_twice")["total"]
    assert metric_twice == 2

    response_once = api_client.get("/anything/bar/123")
    assert response_once.status_code == 200

    analytics = application.threescale_client.analytics
    metric_once = analytics.list_by_service(application["service_id"],
                                            metric_name="metric_once")["total"]
    assert metric_once == 1
