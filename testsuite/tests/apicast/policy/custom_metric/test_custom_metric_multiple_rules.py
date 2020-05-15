"""
When the custom metric policy is configured with more rules, the
response complaining to all of the rules will increase the corresponding metrics
"""

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import rawobj, TESTED_VERSION # noqa # pylint: disable=unused-import

pytestmark = pytest.mark.skipif("TESTED_VERSION < Version('2.9')")


@pytest.fixture(scope="module")
def service(service):
    """
    Creates a foo and foo_200 metrics
    Adds the custom metric policy configured to increase the foo metric on
    200 response and the foo_{{status}} metric on 200 response
    """
    proxy = service.proxy.list()
    service.metrics.create(rawobj.Metric("foo"))
    service.metrics.create(rawobj.Metric("foo_200"))

    proxy.update()

    proxy.policies.insert(0, rawobj.PolicyConfig("custom_metrics", {
        "rules": [{"metric": "foo",
                   "increment": "1",
                   "condition": {
                       "operations": [{
                           "right": "{{status}}",
                           "right_type": "liquid",
                           "left": "200",
                           "op": "=="
                       }],
                       "combine_op": "and"
                   }},
                  {"metric": "foo_{{status}}",
                   "increment": "2",
                   "condition": {
                       "operations": [{
                           "right": "{{status}}",
                           "right_type": "liquid",
                           "left": "200",
                           "op": "=="
                       }],
                       "combine_op": "and"
                   }}
                  ]}))
    return service


def test_metrics_correctly_incremented(application, api_client, threescale):
    """
    Sends a request producing a 200 response
    Asserts that both foo and foo_200 metrics have been increased
    """
    analytics = threescale.analytics

    response = api_client.get("/status/200")
    assert response.status_code == 200
    hits_foo = analytics.list_by_service(application["service_id"], metric_name="foo")["total"]
    hits_foo_200 = analytics.list_by_service(application["service_id"], metric_name="foo_200")["total"]
    assert hits_foo_200 == 2
    assert hits_foo == 1
