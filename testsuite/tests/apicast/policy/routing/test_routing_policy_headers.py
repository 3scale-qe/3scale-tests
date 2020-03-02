"""
Rewrite spec/functional_specs/policies/routing/routing_by_header_spec.rb
"""
from urllib.parse import urlparse
import pytest

from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def service(service, private_base_url):
    """
    Set policy settings
    """
    test_header = {"operations": [
        {"op": "==", "value": "{{ service.id }}", "value_type": "liquid", "match": "header",
         "header_name": "Test-Header"}]}
    proxy = service.proxy.list()
    proxy.policies.insert(0, {
        "name": "routing",
        "version": "builtin",
        "enabled": True,
        "configuration": {
            "rules": [{"url": private_base_url("httpbin"), "condition": test_header}]}})
    return service


@pytest.mark.smoke
def test_routing_policy_with_header(api_client, service):
    """
    Test for the request send with Test-Header and matching value
    """
    response = api_client.get("/get", headers={"Test-Header": str(service["id"])})
    echoed_request = EchoedRequest.create(response)
    assert response.status_code == 200
    assert echoed_request.headers["Host"] == "httpbin.org"


def test_routing_policy_with_header_without_id(api_client, private_base_url):
    """
    Test for the request send with Test-Header without matching value
    """
    parsed_url = urlparse(private_base_url())
    response = api_client.get("/get", headers={"Test-Header": "Not-Service-ID"})
    echoed_request = EchoedRequest.create(response)
    assert response.status_code == 200
    assert echoed_request.headers["Host"] == parsed_url.hostname


def test_routing_policy_without_header(api_client, private_base_url):
    """
     Test for the request send without Test-Header
    """
    parsed_url = urlparse(private_base_url())
    response = api_client.get("/get")
    echoed_request = EchoedRequest.create(response)
    assert response.status_code == 200
    assert echoed_request.headers["Host"] == parsed_url.hostname
