"""
Rewrite spec/functional_specs/policies/ip_check/ip_check_forward_blacklist_spec.rb
"""
import pytest

from testsuite import rawobj


@pytest.fixture(scope="module")
def policy_settings(ip4_addresses):
    "Update policy settings"
    return rawobj.PolicyConfig("ip_check", {
        "ips": ip4_addresses, "check_type": "blacklist",
        "client_ip_sources": ["X-Forwarded-For"]})


def test_ip_check_policy_ip_blacklisted(api_client):
    "Test must reject the request since IP is blacklisted"
    request = api_client.get("/get")
    assert request.status_code == 403
