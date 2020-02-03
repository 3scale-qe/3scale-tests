"""
Rewrite spec/functional_specs/policies/batcher/batcher_policy_prepend_spec.rb
"""
from time import sleep

import pytest


@pytest.fixture(scope="module")
def service(service):
    """
    Set policy settings
    """
    proxy = service.proxy.list()
    proxy.policies.insert(0, {
        "name": "3scale_batcher",
        "version": "builtin",
        "enabled": True,
        "configuration": {
            "batch_report_seconds": 50
        }
    })

    return service


def test_batcher_policy_prepend(api_client, application):
    """
    Test if return correct number of usages of a service in batch
    """
    analytics = application.threescale_client.analytics
    usage_before = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    for _ in range(5):
        api_client.get("/get")
    usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    assert usage_after == usage_before
    sleep(50)
    usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    assert usage_after == usage_before + 5
