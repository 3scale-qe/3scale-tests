"""
Rewrite spec/functional_specs/policies/ip_check/ip_check_forward_whitelist_spec.rb
"""

from packaging.version import Version  # noqa # pylint: disable=unused-import

import pytest

from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import

pytestmark = [pytest.mark.nopersistence]


@pytest.fixture(scope="module")
def policy_settings(ip4_addresses):
    """Update policy settings"""
    return rawobj.PolicyConfig(
        "ip_check", {"check_type": "whitelist", "client_ip_sources": ["X-Forwarded-For"], "ips": ip4_addresses}
    )


def test_ip_check_policy_ip_blacklisted(api_client):
    """Test must accept the request since IP is whitelisted"""
    response = api_client().get("/get")
    assert response.status_code == 200


@pytest.mark.parametrize(
    "ip_addresses,status_code",
    [
        (None, 200),
        (["10.10.10.10"], 403),
        pytest.param(
            [","],
            403,
            marks=[
                pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7076"),
                pytest.mark.skipif("TESTED_VERSION < Version('2.11')"),
            ],
        ),
        pytest.param(
            [",10.10.10.10"],
            403,
            marks=[
                pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7075"),
                pytest.mark.skipif("TESTED_VERSION < Version('2.11')"),
            ],
        ),
    ],
)
def test_ips_with_random_port(ip_addresses, status_code, api_client, ip4_addresses):
    """
    Test must pass all the ip4 addresses with port because that are white listed.
    Test must reject the ip4 addresses that are not whitelisted.
    Test must reject the invalid ip4 addresses starting with comma.
    """
    ip_addresses = ip_addresses or ip4_addresses

    client = api_client()
    for ip_address in ip_addresses:
        response = client.get("/get", headers={"X-Forwarded-For": f"{ip_address}:12345"})
        assert response.status_code == status_code, f"failed on ip: {ip_address}"
