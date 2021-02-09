"""
Test caching policy with allow mode.
"""
from time import sleep
import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import
from testsuite.gateways.gateways import Capability

pytestmark = [pytest.mark.skipif("TESTED_VERSION < Version('2.9.1')"),
              pytest.mark.disruptive,
              pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY),
              pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5753")]
BATCH_REPORT_SECONDS = 50


@pytest.fixture(scope="module")
def service(service):
    """
    Adds policies to service with ALLOW mode.
    Sets the frequency of batch reports that APIcast sends to the 3Scale backend. (Default is 10)
    """
    batcher = rawobj.PolicyConfig("3scale_batcher",
                                  {"batch_report_seconds": BATCH_REPORT_SECONDS, "auths_ttl": BATCH_REPORT_SECONDS})
    caching = rawobj.PolicyConfig("caching", {"caching_type": "allow"})
    service.proxy.list().policies.insert(0, batcher, caching)
    return service


def test_caching_policy_allow_mod(prod_client, openshift, application):
    """
    Test caching policy with caching mode set to ALLOW
        - makes request to production gateway with valid credentials
        - makes request to production gateway with invalid credentials
        - scales apicast-production and backend-listener down to 0
    tests if:
        - response with valid credentials have status_code == 200
        - response with same invalid credentials as before have status_code == 200
    - scales back backend-listener up to starting value
    - if returns correct number of usages of a service in batch after backend and apicast were unavailable
    """
    openshift = openshift()
    replicas = openshift.get_replicas("backend-listener")
    replicas_apicast = openshift.get_replicas("apicast-production")
    client = prod_client(application)

    response = client.get("/", params=None)
    assert response.status_code == 200
    response = client.get("/", params={"user_key": ":user_key"})
    assert response.status_code == 403

    openshift.scale("apicast-production", 0)
    openshift.scale("backend-listener", 0)

    openshift.scale("apicast-production", replicas_apicast)

    analytics = application.threescale_client.analytics
    usage_before = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]

    try:
        # Test if response succeed on production calls with valid credentials
        response = client.get("/", params=None)
        assert response.status_code == 200

        # Test if response succeed on production calls with known invalid credentials
        # It will succeed because apicast was redeployed (cache is empty)
        response = client.get("/", params={"user_key": ":user_key"})
        assert response.status_code == 200

        usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
        assert usage_after == usage_before
    finally:
        openshift.scale("backend-listener", replicas)

    # BATCH_REPORT_SECONDS needs to be big enough to execute all the requests to apicast + assert on analytics
    sleep(BATCH_REPORT_SECONDS + 1)

    usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    assert usage_after == usage_before + 1
