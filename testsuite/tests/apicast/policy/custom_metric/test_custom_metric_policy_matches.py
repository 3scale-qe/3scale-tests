"""
When a service is configured with the custom metrics policy matching a
responses where status code matches a regex, the response with a passing
status code increases the metric defined in the policy.
"""
import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import rawobj, TESTED_VERSION # noqa # pylint: disable=unused-import

pytestmark = pytest.mark.skipif("TESTED_VERSION < Version('2.9')")


@pytest.fixture(scope="module")
def service(service):
    """
    Adds foo metric
    Adds custom_metrics policy configured to increment foo metric
    when a response contains any 4.. status code
    """
    proxy = service.proxy.list()
    service.metrics.create(rawobj.Metric("foo"))
    proxy.update()

    proxy.policies.insert(0, rawobj.PolicyConfig("custom_metrics", {
        "rules": [{"metric": "foo",
                   "increment": "1",
                   "condition": {
                       "operations": [{
                           "left": "{{status}}",
                           "left_type": "liquid",
                           "right": "4..",
                           "op": "matches"
                       }],
                       "combine_op": "and"
                   }}]}))
    return service


@pytest.mark.parametrize("status_code,hits", [(403, 1), (402, 1), (500, 0)])
def test_metrics_correctly_incremented(application, api_client, threescale, status_code,
                                       hits):
    """
    Sends requests producing responses with a (403, 402, 500) status codes
    Asserts that the foo metric has increased by (1, 1, 0) for the corresponding call.
    """
    analytics = threescale.analytics

    hits_before = analytics.list_by_service(application["service_id"], metric_name="foo")["total"]
    response = api_client.get("/status/" + str(status_code))
    assert response.status_code == status_code
    hits_after = analytics.list_by_service(application["service_id"], metric_name="foo")["total"]
    assert hits_after - hits_before == hits
