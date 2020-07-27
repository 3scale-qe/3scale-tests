"""
Rewrite spec/functional_specs/policies/combination/caching_batching_policy_spec.rb
https://issues.jboss.org/browse/THREESCALE-2705
"""
from time import sleep

import pytest

from testsuite import rawobj
from testsuite.gateways.gateways import Capability


@pytest.fixture(scope="module")
def service(service):
    """Adds policies to servies"""
    service.proxy.list().policies.append(rawobj.PolicyConfig("3scale_batcher", {"batch_report_seconds": 50}),
                                         rawobj.PolicyConfig("caching", {"caching_type": "allow"}))
    return service


@pytest.mark.disruptive
# TODO: flaky because ocp4 won't scale the pod to 0, we need to use apimanager object to change replicas
@pytest.mark.flaky
@pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY)
def test_batcher_caching_policy(prod_client, application, openshift):
    """Test if return correct number of usages of a service in batch after backend was unavailable"""
    openshift = openshift()
    replicas = openshift.get_replicas("backend-listener")
    client = prod_client(application, version=2)
    response = client.get("/", params=None)
    assert response.status_code == 200
    response = client.get("/", params={"user_key": ":user_key"})
    assert response.status_code == 403
    openshift.scale("backend-listener", 0)

    analytics = application.threescale_client.analytics
    usage_before = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]

    try:
        # Test if response succeed on production calls with valid credentials
        for _ in range(3):
            response = client.get("/", params=None)
            assert response.status_code == 200

        # Test if response fail on production calls with known invalid credentials
        for _ in range(3):
            response = client.get("/", params={"user_key": ":user_key"})
            assert response.status_code == 403

        usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
        assert usage_after == usage_before
    finally:
        openshift.scale("backend-listener", replicas)
    sleep(50)

    usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    assert usage_after == usage_before + 4
