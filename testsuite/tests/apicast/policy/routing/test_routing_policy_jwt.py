"""
Rewrite spec/functional_specs/policies/routing/routing_by_jwt_spec.rb
"""
from urllib.parse import urlparse

import pytest
from testsuite import rawobj
from testsuite.rhsso.rhsso import OIDCClientAuthHook
from testsuite.echoed_request import EchoedRequest
from testsuite.utils import blame


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(lifecycle_hooks, rhsso_service_info):
    """Have application/service with RHSSO auth configured"""

    lifecycle_hooks.append(OIDCClientAuthHook(rhsso_service_info))


@pytest.fixture(scope="module")
def second_application(custom_application, custom_app_plan, service, lifecycle_hooks, request):
    "Create a second application"
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "CustAPlan")), service)
    app = custom_application(rawobj.Application(blame(request, "CustApp-test"), plan), hooks=lifecycle_hooks)
    return app


@pytest.fixture(scope="module", autouse=True)
def service_update(service, second_application, private_base_url):
    "Update service policy"
    test_jwt = {"operations": [
        {"op": "==", "value": second_application["client_id"], "match": "jwt_claim", "jwt_claim_name": "azp"}]}
    proxy = service.proxy.list()
    proxy.policies.insert(0, rawobj.PolicyConfig("routing", {"rules": [{"url": private_base_url("echo-api"),
                                                                        "condition": test_jwt}]}))


def test_routing_policy_jwt_httpbin(api_client, private_base_url):
    """Test for the request send without matching value to httpbin"""
    parsed_url = urlparse(private_base_url())
    response = api_client.get("/get")
    echoed_request = EchoedRequest.create(response)
    assert response.status_code == 200
    assert echoed_request.headers["Host"] == parsed_url.hostname
    assert response.request.headers["Authorization"].startswith("Bearer")  # RHSSO used?


def test_routing_policy_jwt_echo_api(second_application, testconfig, private_base_url):
    """Test for the request send with matching value to echo api"""
    parsed_url = urlparse(private_base_url("echo-api"))
    api_client = second_application.api_client(verify=testconfig["ssl_verify"])
    response = api_client.get("/get")
    assert response.status_code == 200
    echoed_request = EchoedRequest.create(response)
    assert echoed_request.path == "/get"
    assert echoed_request.headers["Host"] == parsed_url.hostname
