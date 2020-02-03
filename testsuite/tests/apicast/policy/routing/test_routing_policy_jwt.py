"""
Rewrite spec/functional_specs/policies/routing/routing_by_jwt_spec.rb
"""
from urllib.parse import urlparse

import pytest
from threescale_api.resources import Service
from testsuite import rawobj
from testsuite.rhsso.rhsso import OIDCClientAuth
from testsuite.echoed_request import EchoedRequest
from testsuite.utils import randomize


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
def second_application(custom_application, custom_app_plan, service, rhsso_service_info):
    "Create a second application"
    plan = custom_app_plan(rawobj.ApplicationPlan(randomize("CustomAppPlan")), service)
    app = custom_application(rawobj.Application(randomize("CustomApp-test"), plan))
    app.register_auth("oidc", OIDCClientAuth(rhsso_service_info))
    return app


@pytest.fixture(scope="module", autouse=True)
def service_update(service, second_application, backend):
    "Update service policy"
    test_jwt = {"operations": [
        {"op": "==", "value": second_application["client_id"], "match": "jwt_claim", "jwt_claim_name": "azp"}]}
    proxy = service.proxy.list()
    proxy.policies.insert(0, rawobj.PolicyConfig("routing", {"rules": [{"url": backend("echo-api"),
                                                                        "condition": test_jwt}]}))


def test_routing_policy_jwt_httpbin(api_client, backend):
    """Test for the request send without matching value to httpbin"""
    parsed_url = urlparse(backend())
    response = api_client.get("/get")
    echoed_request = EchoedRequest.create(response)
    assert response.status_code == 200
    assert echoed_request.headers["Host"] == parsed_url.hostname


def test_routing_policy_jwt_echo_api(second_application, testconfig, backend):
    """Test for the request send with matching value to echo api"""
    parsed_url = urlparse(backend("echo-api"))
    api_client = second_application.api_client(verify=testconfig["ssl_verify"])
    response = api_client.get("/get")
    assert response.status_code == 200
    echoed_request = EchoedRequest.create(response)
    assert echoed_request.path == "/get"
    assert echoed_request.headers["Host"] == parsed_url.hostname
