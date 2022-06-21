"""
Rewrite spec/functional_specs/policies/ip_check/ip_check_real_ip_blacklist_spec.rb
"""
import pytest

from testsuite import rawobj

pytestmark = [pytest.mark.nopersistence]


@pytest.fixture(scope="module")
def service(service):
    """Update policy settings"""
    proxy = service.proxy.list()
    proxy.policies.append(rawobj.PolicyConfig("ip_check", {"ips": ['10.10.10.10', '10.100.10.0/24'],
                                                           "check_type": "blacklist",
                                                           "client_ip_sources": ["X-Real-IP"]}))

    return service


def test_ip_check_policy_ip_blacklisted(api_client):
    """test must reject the request since IP is blacklisted"""
    response = api_client().get("/get", headers={"X-Real-IP": "10.10.10.10"})
    assert response.status_code == 403


def test_ip_check_policy_ip_not_blacklisted(api_client):
    """test must accept the request since IP is not blacklisted"""
    response = api_client().get("/get", headers={"X-Real-IP": "10.10.10.25"})
    assert response.status_code == 200
