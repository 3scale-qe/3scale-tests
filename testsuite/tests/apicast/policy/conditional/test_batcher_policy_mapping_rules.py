"""
Test checks that batcher policy works with conditional policy.
"""

from time import sleep

import pytest
from packaging.version import Version

from testsuite import TESTED_VERSION, rawobj

pytestmark = [
    pytest.mark.nopersistence,
    pytest.mark.skipif(TESTED_VERSION < Version("2.16"), reason="TESTED_VERSION < Version('2.16')"),
]

BATCH_REPORT_SECONDS = 50


@pytest.fixture(scope="module")
def policy_settings():
    """Set policy settings"""
    return rawobj.PolicyConfig(
        "conditional",
        {
            "condition": {
                "operations": [
                    {"left": "{{ uri }}", "left_type": "liquid", "op": "==", "right": "/get1", "right_type": "plain"}
                ]
            },
            "policy_chain": [
                {"name": "3scale_batcher", "configuration": {"batch_report_seconds": BATCH_REPORT_SECONDS}}
            ],
        },
    )


@pytest.fixture(scope="module")
def service(service):
    """
    Add the mapping rules
    """
    proxy = service.proxy.list()

    metric1 = service.metrics.list()[0]
    metric2 = service.metrics.create(rawobj.Metric("name2"))

    # delete implicit '/' rule
    proxy.mapping_rules.list()[0].delete()

    proxy.mapping_rules.create(rawobj.Mapping(metric1, pattern="/get1"))
    proxy.mapping_rules.create(rawobj.Mapping(metric2, pattern="/get2"))

    proxy.deploy()

    return service


@pytest.fixture(scope="module")
def client(api_client):
    """We are testing path that doesn't match mapping rule so we need to disable retry"""
    assert api_client().get("/get1").status_code == 200  # Ensures that service is set up correctly
    assert api_client().get("/get2").status_code == 200  # Ensures that service is set up correctly

    # Due to the batcher policy, hits to the service are only shown every 50 seconds,
    # so we have to wait 50 seconds to ensure that this call does not affect the test.
    sleep(BATCH_REPORT_SECONDS)

    return api_client(disable_retry_status_list={404})


def test_batcher_policy_append(client, service, application):
    """Test if return correct number of usages of a service in batch
    when condition is met and when it is not."""
    analytics = application.threescale_client.analytics
    usage_before1 = analytics.list_by_service(service["id"], metric_name="hits")["total"]
    usage_before2 = analytics.list_by_service(service["id"], metric_name="name2")["total"]

    for i in range(3):
        response = client.get("/get1")
        assert response.status_code == 200, f"{i}. iteration was unsuccessful"

        response = client.get("/anything/no_mapping_rule_match")
        assert response.status_code == 404, f"{i}. iteration was unsuccessful"

        response = client.get("/get2")
        assert response.status_code == 200, f"{i}. iteration was unsuccessful"

    usage_after1 = analytics.list_by_service(service["id"], metric_name="hits")["total"]
    assert usage_after1 == usage_before1

    usage_after2 = analytics.list_by_service(service["id"], metric_name="name2")["total"]
    assert usage_after2 == usage_before2 + 3

    sleep(BATCH_REPORT_SECONDS)

    usage_after1 = analytics.list_by_service(service["id"], metric_name="hits")["total"]
    assert usage_after1 == usage_before1 + 3

    usage_after2 = analytics.list_by_service(service["id"], metric_name="name2")["total"]
    assert usage_after2 == usage_before2 + 3
