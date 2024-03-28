"""
    Test checks that mapping rules are working with batcher policy
"""

from time import sleep
import pytest

from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import


pytestmark = [
    pytest.mark.nopersistence,
    pytest.mark.skipif("TESTED_VERSION < Version('2.9')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5513"),
]


@pytest.fixture(scope="module")
def policy_settings():
    """Set policy settings"""
    return rawobj.PolicyConfig("3scale_batcher", {"batch_report_seconds": 50})


@pytest.fixture(scope="module")
def service(service):
    """
    Add the mapping rules
    """
    proxy = service.proxy.list()

    metric = service.metrics.list()[0]

    # delete implicit '/' rule
    proxy.mapping_rules.list()[0].delete()

    proxy.mapping_rules.create(rawobj.Mapping(metric, pattern="/get"))

    proxy.deploy()

    return service


@pytest.fixture(scope="module")
def client(api_client):
    """We are testing path that doesn't match mapping rule so we need to disable retry"""
    assert api_client().get("/get").status_code == 200  # Ensures that service is set up correctly

    # Due to the batcher policy, hits to the service are only shown every 50 seconds,
    # so we have to wait 50 seconds to ensure that this call does not affect the test.
    sleep(50)

    return api_client(disable_retry_status_list={404})


def test_batcher_policy_append(client, application):
    """Test if return correct number of usages of a service in batch"""
    analytics = application.threescale_client.analytics
    usage_before = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]

    for i in range(3):
        response = client.get("/get")
        assert response.status_code == 200, f"{i}. iteration was unsuccessful"

        response = client.get("/anything/no_mapping_rule_match")
        assert response.status_code == 404, f"{i}. iteration was unsuccessful"

    usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    assert usage_after == usage_before

    sleep(50)

    usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    assert usage_after == usage_before + 3
