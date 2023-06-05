"""
Tests upstream mTLS policy with standard gateway, which enables mTLS between APIcast and upstream api (httpbin)

It uses two configuration of custom deployed Httpbin:
First with matching certificates and authorities, which should succeed with 200
Second with mismatched certificates, which should fail with 502 due to httpbin refusing to accept the other certificate

It tests only embedded type as path requires manipulation with the deployment
"""
import pytest

from testsuite import rawobj, gateways
from testsuite.capabilities import Capability
from testsuite.certificates import Certificate
from testsuite.tests.apicast.policy.tls import embedded

pytestmark = [pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT)]


@pytest.fixture(scope="session")
def invalid_authority(request, manager, testconfig) -> Certificate:
    """To be used in tests validating server certificates"""
    certificate_authority = manager.get_or_create_ca("invalid_ca", hosts=["*.com"])
    if not testconfig["skip_cleanup"]:
        request.addfinalizer(certificate_authority.delete_files)
    return certificate_authority


@pytest.fixture(scope="session")
def staging_gateway(request, testconfig):
    """Standard gateway, copied from root conftest."""
    gateway = gateways.gateway(staging=True)
    if not testconfig["skip_cleanup"]:
        request.addfinalizer(gateway.destroy)
    gateway.create()

    return gateway


@pytest.fixture(scope="module")
def policy_settings(certificate):
    """Embedded upstream mTLS policy"""
    embedded_cert = embedded(certificate.certificate, "tls.crt", "pkix-cert")
    embedded_key = embedded(certificate.key, "tls.key", "x-iwork-keynote-sffkey")
    return rawobj.PolicyConfig(
        "upstream_mtls",
        {
            "certificate_type": "embedded",
            "certificate_key_type": "embedded",
            "certificate": embedded_cert,
            "certificate_key": embedded_key,
        },
    )


def test_mtls_request(api_client, authority_and_code):
    """Test that mtls request returns correct status code"""
    _, code = authority_and_code
    assert api_client().get("/get").status_code == code
