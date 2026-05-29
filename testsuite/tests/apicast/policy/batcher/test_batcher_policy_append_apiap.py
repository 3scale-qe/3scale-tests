"""
Test batcher_policy with added backend.
"""

from time import sleep

import pytest

from testsuite import rawobj

BATCH_REPORT_SECONDS = 50


@pytest.fixture(scope="module")
def policy_settings():
    """Set policy settings"""
    return rawobj.PolicyConfig("3scale_batcher", {"batch_report_seconds": BATCH_REPORT_SECONDS})


@pytest.fixture(scope="module")
def backends_mapping(custom_backend):
    """Creates custom backends with paths "/lib", "/bin"""
    return {"/lib": custom_backend("backend"), "/bin": custom_backend("backend2")}


def test_batcher_policy_append(api_client, application):
    """Test if return correct number of usages of a service in batch for both backends"""
    client = api_client()
    analytics = application.threescale_client.analytics
    usage_before = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]

    for _ in range(3):
        client.get("/lib/get")
        client.get("/bin/get")

    usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    assert usage_after == usage_before

    sleep(BATCH_REPORT_SECONDS + 1)

    usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    assert usage_after == usage_before + 6
