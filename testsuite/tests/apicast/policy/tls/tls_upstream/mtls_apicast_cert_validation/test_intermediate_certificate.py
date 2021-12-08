"""
Tests then when the APIcast is sending a certificate chain to the upstream API,
all certificates in the chain are sent and the request is correctly validated.
"""
import pytest

from testsuite import rawobj
from testsuite.capabilities import Capability
from testsuite.tests.apicast.policy.tls import embedded


pytestmark = [
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7363")]


@pytest.fixture(scope="module")
def upstream_authority(valid_authority):
    """
    Authority of the upstream API used to validate certificates sent from APIcast.
    """
    return valid_authority


@pytest.fixture(scope="module")
def intermediate_authority(request, configuration, valid_authority):
    """
    Intermediate_authority
    valid_authority -> intermediate_authority
    """
    authority = configuration.manager.get_or_create_ca("intermediate_authority",
                                                       hosts=["*.com"],
                                                       certificate_authority=valid_authority)
    request.addfinalizer(authority.delete_files)
    return authority


@pytest.fixture(scope="module")
def intermediate_signed_certificate(create_cert, intermediate_authority):
    """
    Certificate signed by the intermediate authority
    valid_authority -> intermediate_authority -> intermediate_signed_certificate
    """
    return create_cert("inter_signed_cert", intermediate_authority)


@pytest.fixture(scope="module")
def chained_certificate(chainify, intermediate_signed_certificate, intermediate_authority):
    """
    Client certificate chain containing the intermediate authority
    """
    return chainify(intermediate_signed_certificate, intermediate_authority)


@pytest.fixture(scope="module")
def policy_settings(chained_certificate):
    """
    Sets up the embedded upstream mTLS policy
    """
    embedded_cert = embedded(chained_certificate.certificate, "tls.crt", "pkix-cert")
    embedded_key = embedded(chained_certificate.key, "tls.key", "x-iwork-keynote-sffkey")
    return rawobj.PolicyConfig("upstream_mtls", {"certificate_type": "embedded",
                                                 "certificate_key_type": "embedded",
                                                 "certificate": embedded_cert,
                                                 "certificate_key": embedded_key})


def test_mtls_chained_request(api_client):
    """
    Test that mtls request containing chained certificate returns 200 status code
    """
    client = api_client()

    response = client.get("/get")
    assert response.status_code == 200
