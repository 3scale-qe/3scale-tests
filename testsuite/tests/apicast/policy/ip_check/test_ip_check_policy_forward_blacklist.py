"""
Rewrite spec/functional_specs/policies/ip_check/ip_check_forward_blacklist_spec.rb
"""
import pytest

from testsuite import rawobj

pytestmark = [pytest.mark.nopersistence]


@pytest.fixture(scope="module")
def policy_settings(ip4_addresses):
    """Update policy settings"""
    return rawobj.PolicyConfig(
        "ip_check", {"ips": ip4_addresses, "check_type": "blacklist", "client_ip_sources": ["X-Forwarded-For"]}
    )


def test_ip_check_policy_ip_blacklisted(api_client):
    """Test must reject the request since IP is blacklisted"""
    response = api_client().get("/get")
    assert response.status_code == 403


def test_ips_with_random_port(api_client, ip4_addresses):
    """
    Test must reject all the ip4 addresses with port that are blacklisted.
    """
    client = api_client()

    for ip_address in ip4_addresses:
        response = client.get("/get", headers={"X-Forwarded-For": f"{ip_address}:12345"})
        assert response.status_code == 403, f"failed on ip: {ip_address}"
