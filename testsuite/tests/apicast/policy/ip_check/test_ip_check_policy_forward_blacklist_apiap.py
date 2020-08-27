"""
Test ip_check_policy_forward with added backend.
"""
import pytest

from testsuite import rawobj


@pytest.fixture(scope="module")
def backends_mapping(custom_backend):
    """Creates custom backends with paths "/bin", "/lib"""
    return {"/bin": custom_backend("backend"), "/lib": custom_backend("backend2")}


@pytest.fixture(scope="module")
def policy_settings(ip4_addresses):
    """Update policy settings"""
    return rawobj.PolicyConfig("ip_check", {
        "ips": ip4_addresses, "check_type": "blacklist",
        "client_ip_sources": ["X-Forwarded-For"]})


@pytest.mark.parametrize("backend", ["/bin", "/lib"])
def test_ip_check_policy_ip_blacklisted(api_client, backend):
    """Test must reject the request since IP is blacklisted"""
    request = api_client.get(f'{backend}/get')
    assert request.status_code == 403


@pytest.mark.parametrize("backend", ["/bin", "/lib"])
def test_ips_with_random_port(api_client, ip4_addresses, backend):
    """Test must reject all the ip4 addresses with port that are blacklisted."""
    for ip_address in ip4_addresses:
        request = api_client.get(f'{backend}/get', headers={'X-Forwarded-For': f"{ip_address}:12345"})
        assert request.status_code == 403, f"failed on ip: {ip_address}"
