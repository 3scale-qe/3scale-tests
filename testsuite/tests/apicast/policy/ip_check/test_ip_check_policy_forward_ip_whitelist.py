"""
Rewrite spec/functional_specs/policies/ip_check/ip_check_forward_whitelist_spec.rb
"""
import pytest

from testsuite import rawobj


@pytest.fixture(scope="module")
def policy_settings(ip4_addresses):
    """Update policy settings"""
    return rawobj.PolicyConfig("ip_check", {
        "check-type": "whitelist",
        "client_ip_sources": ["X-Forwarded-For"],
        "ips_list": ip4_addresses
    })


def test_ip_check_policy_ip_blacklisted(api_client):
    """Test must accept the request since IP is whitelisted"""
    response = api_client().get("/get")
    assert response.status_code == 200


def test_ips_with_random_port(api_client, ip4_addresses):
    """
    Test must pass all the ip4 addresses with port because that are white listed.
    """
    client = api_client()
    for ip_address in ip4_addresses:
        response = client.get('/get', headers={'X-Forwarded-For': f"{ip_address}:12345"})
        assert response.status_code == 200, f"failed on ip: {ip_address}"
