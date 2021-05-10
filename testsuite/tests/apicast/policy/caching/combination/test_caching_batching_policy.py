"""
Rewrite spec/functional_specs/policies/combination/caching_batching_policy_spec.rb
"""
from time import sleep

import pytest

from testsuite import rawobj
from testsuite.capabilities import Capability

BATCH_REPORT_SECONDS = 150


@pytest.fixture(scope="module")
def service(service):
    """Adds policies to servies"""
    service.proxy.list().policies.append(
        rawobj.PolicyConfig("3scale_batcher", {"batch_report_seconds": BATCH_REPORT_SECONDS}),
        rawobj.PolicyConfig("caching", {"caching_type": "allow"}))
    return service


@pytest.mark.issue("https://issues.jboss.org/browse/THREESCALE-2705")
@pytest.mark.required_capabilities(Capability.SCALING)
def test_batcher_caching_policy(prod_client, application, openshift):
    """Test if return correct number of usages of a service in batch after backend was unavailable"""
    client = prod_client(application)
    client.auth = None
    auth = application.authobj()

    response = client.get("/", auth=auth)
    assert response.status_code == 200
    response = client.get("/", params={"user_key": ":user_key"})
    assert response.status_code == 403

    with openshift().scaler.scale("backend-listener", 0):
        analytics = application.threescale_client.analytics
        usage_before = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]

        # Test if response succeed on production calls with valid credentials
        for _ in range(3):
            response = client.get("/", auth=auth)
            assert response.status_code == 200

        # Test if response fail on production calls with known invalid credentials
        for _ in range(3):
            response = client.get("/", params={"user_key": ":user_key"})
            assert response.status_code == 403

        usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
        assert usage_after == usage_before

    # BATCH_REPORT_SECONDS needs to be big enough to execute all the requests to apicast + assert on analytics
    sleep(BATCH_REPORT_SECONDS + 1)

    usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    assert usage_after == usage_before + 4
