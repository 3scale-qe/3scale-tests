"""
Rewrite spec/functional_specs/policies/batcher/batcher_policy_oidc_spec.rb
"""
from time import sleep
import pytest

from testsuite import rawobj
from testsuite.rhsso.rhsso import OIDCClientAuthHook


BATCH_REPORT_SECONDS = 50


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(lifecycle_hooks, rhsso_service_info):
    """Have application/service with RHSSO auth configured"""

    lifecycle_hooks.append(OIDCClientAuthHook(rhsso_service_info))


@pytest.fixture(scope="module")
def policy_settings():
    """Set policy settings"""
    return rawobj.PolicyConfig("3scale_batcher", {"batch_report_seconds": BATCH_REPORT_SECONDS})


@pytest.mark.sandbag  # slow due to long sleep
def test_batcher_policy_oidc(api_client, application, rhsso_service_info):
    """Test if return correct number of usages of a service in batch"""
    app_key = application.keys.list()["keys"][0]["key"]["value"]
    token = rhsso_service_info.password_authorize(application["client_id"], app_key).token['access_token']
    analytics = application.threescale_client.analytics
    usage_before = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    client = api_client()

    for _ in range(5):
        response = client.get("/get", headers={'access_token': token})

    assert response.request.headers["Authorization"].startswith("Bearer")  # RHSSO used?
    usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    assert usage_after == usage_before

    # BATCH_REPORT_SECONDS needs to be big enough to execute all the requests to apicast + assert on analytics
    sleep(BATCH_REPORT_SECONDS + 1)

    usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    assert usage_after == usage_before + 5
