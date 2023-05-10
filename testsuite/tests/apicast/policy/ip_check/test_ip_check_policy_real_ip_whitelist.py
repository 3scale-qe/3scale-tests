"""
Rewrite spec/functional_specs/policies/ip_check/ip_check_real_ip_whitelist_spec.rb
"""

import pytest
from testsuite import rawobj

pytestmark = [pytest.mark.nopersistence]


@pytest.fixture(scope="module")
def policy_settings():
    """Update policy settings"""

    return rawobj.PolicyConfig(
        "ip_check", {"ips": ["10.10.10.10"], "check_type": "whitelist", "client_ip_sources": ["X-Real-IP"]}
    )


def test_ip_check_policy_ip_whitelisted(api_client):
    """test must accept the request since the IP is whitelisted"""

    response = api_client().get("/get", headers={"X-Real-IP": "10.10.10.10"})
    assert response.status_code == 200


def test_ip_check_policy_ip_not_whitelisted(api_client):
    """test must reject the request since the IP is not whitelisted"""

    response = api_client().get("/get", headers={"X-Real-IP": "10.10.10.11"})
    assert response.status_code == 403
