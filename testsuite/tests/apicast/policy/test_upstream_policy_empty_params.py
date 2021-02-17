"""
Rewrite spec/functional_specs/policies/upstream_rewrite/nil_added_when_empty_params_spec.rb
"""
import pytest

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def service_proxy_settings(service_proxy_settings):
    """Set headers as credentials location"""
    # By default credentials are located in query, and we need query to be empty
    service_proxy_settings.update(credentials_location="headers")
    return service_proxy_settings


@pytest.fixture(scope="module")
def service(service, private_base_url):
    """Add upstream policy"""
    proxy = service.proxy.list()
    proxy.policies.insert(0, rawobj.PolicyConfig("upstream", {
        "rules": [{"url": private_base_url("echo_api"), "regex": "v1"}]}))

    return service


@pytest.mark.issue("https://issues.jboss.org/browse/THREESCALE-1506")
def test_upstream_policy_empty_params(api_client):
    """
    Test if it redirect to the echo-api without nil params
    """
    client = api_client()

    response = client.get("/v1")
    assert response.status_code == 200
    echoed_request = EchoedRequest.create(response)
    assert echoed_request.path == "/v1"
    assert echoed_request.params == ""
