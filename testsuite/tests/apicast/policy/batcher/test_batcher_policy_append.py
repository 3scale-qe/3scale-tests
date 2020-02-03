"""
Rewrite spec/functional_specs/policies/batcher/batcher_policy_append_spec.rb
"""
from time import sleep
import pytest
from testsuite import rawobj


@pytest.fixture(scope="module")
def policy_settings():
    """Set policy settings"""
    return rawobj.PolicyConfig("3scale_batcher", {"batch_report_seconds": 50})


def test_batcher_policy_append(api_client, application):
    """Test if return correct number of usages of a service in batch"""
    analytics = application.threescale_client.analytics
    usage_before = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]

    for _ in range(5):
        api_client.get("/get")

    usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    assert usage_after == usage_before

    sleep(50)

    usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    assert usage_after == usage_before + 5
