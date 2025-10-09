"""
Test checks that batcher policy is working with a metric containing a non-alphanumeric
character in the name
"""

from time import sleep
import pytest

from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import


pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.10')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-4913"),
]


BATCH_REPORT_SECONDS = 50


@pytest.fixture(scope="module")
def policy_settings():
    """Set policy settings"""
    return rawobj.PolicyConfig("3scale_batcher", {"batch_report_seconds": BATCH_REPORT_SECONDS})


@pytest.fixture(scope="module")
def metric_name():
    """
    Name of the metric containing non alphanumerical character ('/')
    """
    return "m/1"


@pytest.fixture(scope="module")
def service(service, metric_name):
    """
    Creates the metric with the metric name and a mapping rule for that metric
    """
    proxy = service.proxy.list()

    metric = service.metrics.create(rawobj.Metric(metric_name))

    # delete implicit '/' rule
    proxy.mapping_rules.list()[0].delete()

    service.proxy.list().mapping_rules.create(rawobj.Mapping(metric, "/", "GET"))
    service.proxy.list().update()

    return service


def test_batcher_policy_append(api_client, application, metric_name):
    """
    Test if the reported numbers of usages are correct
    """
    client = api_client()
    analytics = application.threescale_client.analytics
    usage_before = analytics.list_by_service(application["service_id"], metric_name=metric_name)["total"]

    for i in range(3):
        response = client.get("/anything")
        assert response.status_code == 200, f"{i}. iteration was unsuccessful"

    sleep(BATCH_REPORT_SECONDS + 1)

    usage_after = analytics.list_by_service(application["service_id"], metric_name=metric_name)["total"]
    assert usage_after == usage_before + 3
