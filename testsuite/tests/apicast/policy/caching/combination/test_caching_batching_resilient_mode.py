"""
Test caching policy with strict mode.
"""
from time import sleep
import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import
from testsuite.capabilities import Capability

pytestmark = [pytest.mark.skipif("TESTED_VERSION < Version('2.9.1')"),
              pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5753"),
              pytest.mark.required_capabilities(Capability.SCALING)]
BATCH_REPORT_SECONDS = 150


@pytest.fixture(scope="module")
def service(service):
    """
    Adds policies to service RESILIENT mode.
    Sets the frequency of batch reports that APIcast sends to the 3Scale backend. (Default is 10)
    """
    batcher = rawobj.PolicyConfig("3scale_batcher",
                                  {"batch_report_seconds": BATCH_REPORT_SECONDS, "auths_ttl": BATCH_REPORT_SECONDS})
    caching = rawobj.PolicyConfig("caching", {"caching_type": "resilient"})
    service.proxy.list().policies.insert(0, batcher, caching)
    return service


def test_caching_batching_resilient_mode(prod_client, openshift, application):
    """
    Test caching policy with caching mode set to STRICT
        - makes request to production gateway with valid credentials
        - scales backend-listener down to 0
    tests if:
        - response with valid credentials have status_code == 200
        - response with same invalid credentials as before have status_code == 403
        - response with new valid credentials have status_code == 403
    - scales back backend-listener up to starting value
    - if returns correct number of usages of a service in batch after backend was unavailable
    """
    client = prod_client(application)
    client.auth = None
    auth = application.authobj()

    response = client.get("/", auth=auth)
    assert response.status_code == 200

    analytics = application.threescale_client.analytics
    usage_before = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]

    with openshift().scaler.scale("backend-listener", 0):
        # Test if response succeed on production calls with valid credentials
        response = client.get("/", auth=auth)
        assert response.status_code == 200

        # Test if response fail on production calls with known invalid credentials
        response = client.get("/", params={"user_key": ":user_key"})
        assert response.status_code == 403

        usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
        assert usage_after == usage_before

        response = client.get("/", auth=auth)
        assert response.status_code == 200

    # BATCH_REPORT_SECONDS needs to be big enough to execute all the requests to apicast + assert on analytics
    sleep(BATCH_REPORT_SECONDS + 1)

    usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    assert usage_after == usage_before + 3
