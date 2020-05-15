"""
When the custom metric policy is configured to increase a metric based on
the response, it will increase the corresponding metric
"""
import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import rawobj, TESTED_VERSION # noqa # pylint: disable=unused-import

pytestmark = pytest.mark.skipif("TESTED_VERSION < Version('2.9')")


@pytest.fixture(scope="module")
def service(service):
    """
    Creates a foo_200 and foo_201 metric
    Adds the custom metric policy configured to increment the foo_{{status}} metric,
    where {{status}} is substituted for the response status code
    """
    proxy = service.proxy.list()
    service.metrics.create(rawobj.Metric("foo_200"))
    service.metrics.create(rawobj.Metric("foo_201"))
    proxy.update()

    proxy.policies.insert(0, rawobj.PolicyConfig("custom_metrics", {
        "rules": [{"metric": "foo_{{status}}",
                   "increment": "1",
                   "condition": {
                       "operations": [{
                           "right": "1",
                           "left": "1",
                           "op": "=="
                       }],
                       "combine_op": "and"
                   }}
                  ]}))
    return service


@pytest.mark.parametrize("status_code", [200, 201])
def test_metrics_correctly_incremented(application, api_client, threescale, status_code):
    """
    Sends requests producing 200 and 201 responses
    Asserts that the foo_200 and foo_201 metrics have been increased
    """
    analytics = threescale.analytics

    response = api_client.get("/status/" + str(status_code))
    assert response.status_code == status_code
    hits = analytics.list_by_service(application["service_id"],
                                     metric_name="foo_" + str(status_code))["total"]
    assert hits == 1
