"""
When the custom_metrics policy is configured to increase the metric
by the value from the response header, the metric is increased by the given
value
"""

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import rawobj, TESTED_VERSION # noqa # pylint: disable=unused-import

pytestmark = pytest.mark.skipif("TESTED_VERSION < Version('2.9')")


@pytest.fixture(scope="module")
def service(service):
    """
    Adds the foo metric
    Adds the custom_metrics policy configured to increase the foo metric
    by the value in the response 'increment' header, when the response
    status code equals 200
    """
    proxy = service.proxy.list()
    service.metrics.create(rawobj.Metric("foo"))
    proxy.update()

    proxy.policies.insert(0, rawobj.PolicyConfig("custom_metrics", {
        "rules": [{"metric": "foo",
                   "increment": "{{ resp.headers['increment'] }}",
                   "condition": {
                       "operations": [{
                           "right": "{{status}}",
                           "right_type": "liquid",
                           "left": "200",
                           "op": "=="
                       }],
                       "combine_op": "and"
                   }}]}))

    return service


@pytest.mark.parametrize("increment", [1, 10])
def test_metrics_correctly_incremented(application, api_client, threescale, increment):
    """
    Sends two requests producing 200 response.
    The value of the 'increment' header of the first response is 1
    The value of the 'increment' header of the first response is 10
    Asserts that the foo metric is increased by 1 after the first response
    and by 10 after the second one.
    """
    analytics = threescale.analytics

    hits_before = analytics.list_by_service(application["service_id"], metric_name="foo")["total"]
    response = api_client.get("/response-headers", params={"increment": increment})
    assert response.status_code == 200
    hits_after = analytics.list_by_service(application["service_id"], metric_name="foo")["total"]

    assert hits_after - hits_before == increment
