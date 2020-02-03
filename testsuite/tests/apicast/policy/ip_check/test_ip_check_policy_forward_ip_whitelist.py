"""
Rewrite spec/functional_specs/policies/ip_check/ip_check_forward_whitelist_spec.rb
"""
import pytest

from testsuite import rawobj


@pytest.fixture(scope="module")
def policy_settings(ip4_addresses):
    "Update policy settings"
    return rawobj.PolicyConfig("ip_check", {
        "check-type": "whitelist",
        "client_ip_sources": ["X-Forwarded-For"],
        "ips_list": ip4_addresses
    })


def test_ip_check_policy_ip_blacklisted(api_client):
    "Test must accept the request since IP is whitelisted"
    request = api_client.get("/get")
    assert request.status_code == 200
