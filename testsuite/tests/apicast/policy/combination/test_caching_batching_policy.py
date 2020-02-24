"""
Rewrite spec/functional_specs/policies/combination/caching_batching_policy_spec.rb
https://issues.jboss.org/browse/THREESCALE-2705
"""
from time import sleep

import pytest

from testsuite import rawobj


@pytest.fixture(scope="module")
def service(service):
    """Adds policies to servies"""
    service.proxy.list().policies.append(rawobj.PolicyConfig("3scale_batcher", {"batch_report_seconds": 50}),
                                         rawobj.PolicyConfig("caching", {"caching_type": "allow"}))
    return service


@pytest.fixture
def prod_client(application, testconfig, redeploy_production_gateway):
    """Promote API to the production gateway"""

    application.service.proxy.list().promote(version=2)
    redeploy_production_gateway()

    return application.api_client(endpoint="endpoint", verify=testconfig["ssl_verify"])


def test_batcher_caching_policy(prod_client, application, openshift):
    """Test if return correct number of usages of a service in batch after backend was unavailable"""
    openshift = openshift()
    replicas = openshift.get_replicas("backend-listener")
    response = prod_client.get("/", params=None)
    assert response.status_code == 200
    response = prod_client.get("/", params={"user_key": ":user_key"})
    assert response.status_code == 403
    openshift.scale("backend-listener", 0)

    analytics = application.threescale_client.analytics
    usage_before = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]

    try:
        # Test if response succeed on production calls with valid credentials
        for _ in range(3):
            response = prod_client.get("/", params=None)
            assert response.status_code == 200

        # Test if response fail on production calls with known invalid credentials
        for _ in range(3):
            response = prod_client.get("/", params={"user_key": ":user_key"})
            assert response.status_code == 403

        usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
        assert usage_after == usage_before
    finally:
        openshift.scale("backend-listener", replicas)
    sleep(50)

    usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    assert usage_after == usage_before + 4
