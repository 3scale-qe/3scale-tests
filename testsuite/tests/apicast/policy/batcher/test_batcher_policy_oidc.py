"""
Rewrite spec/functional_specs/policies/batcher/batcher_policy_oidc_spec.rb
"""
from time import sleep
import pytest
from threescale_api.resources import Service

from testsuite import rawobj
from testsuite.rhsso.rhsso import OIDCClientAuth


@pytest.fixture(scope="module")
def service_settings(service_settings):
    "Set auth mode to OIDC"
    service_settings.update(backend_version=Service.AUTH_OIDC)
    return service_settings


@pytest.fixture(scope="module")
def service_proxy_settings(rhsso_service_info, service_proxy_settings):
    "Set OIDC issuer and type"
    service_proxy_settings.update(
        oidc_issuer_endpoint=rhsso_service_info.authorization_url(),
        oidc_issuer_type="keycloak")
    return service_proxy_settings


@pytest.fixture(scope="module")
def service(service):
    "Update OIDC configuration"
    service.proxy.oidc.update(params={
        "oidc_configuration": {
            "standard_flow_enabled": False,
            "direct_access_grants_enabled": True
        }
    })
    return service


@pytest.fixture(scope="module")
def application(rhsso_service_info, application):
    "Add OIDC client authentication"
    application.register_auth("oidc", OIDCClientAuth(rhsso_service_info))
    return application


@pytest.fixture(scope="module")
def policy_settings():
    """Set policy settings"""
    return rawobj.PolicyConfig("3scale_batcher", {"batch_report_seconds": 50})


@pytest.mark.slow
def test_batcher_policy_oidc(api_client, application, rhsso_service_info):
    """Test if return correct number of usages of a service in batch"""
    app_key = application.keys.list()["keys"][0]["key"]["value"]
    token = rhsso_service_info.password_authorize(application["client_id"], app_key).token['access_token']
    analytics = application.threescale_client.analytics
    usage_before = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]

    for _ in range(5):
        api_client.get("/get", headers={'access_token': token})

    usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    assert usage_after == usage_before

    sleep(50)

    usage_after = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    assert usage_after == usage_before + 5
