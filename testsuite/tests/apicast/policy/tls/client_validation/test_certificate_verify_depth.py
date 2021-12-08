"""
Tests for setting maximum TLS client certificate length, which is set with APICAST_HTTPS_VERIFY_DEPTH env parameter
Client certificate length is measure by number of certificates below the main authority:

Length 1: Root -> Certificate
Length 2: Root -> Intermediate -> Certificate

This tests sets up the chain from the root certificate which is trusted by the gateway and then
tests if the certificate is accepted or not.

In general tests with Length =< Depth should pass and tests with Length > Depth should fail
"""
import pytest

from testsuite.capabilities import Capability
from testsuite.certificates import Certificate

pytestmark = pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT)


@pytest.fixture(scope="module")
def valid_authority(staging_gateway):
    """Override valid authority with authority of the staging gateway"""
    return staging_gateway.server_authority


@pytest.fixture(scope="module")
def authority_a(request, manager, valid_authority):
    """
    Intermediate authority_a
    valid_authority -> authority_a
    """
    authority = manager.get_or_create_ca("authority_a",
                                         hosts=["*.com"],
                                         certificate_authority=valid_authority)
    request.addfinalizer(authority.delete_files)
    return authority


@pytest.fixture(scope="module")
def authority_b(request, manager, authority_a):
    """
    Intermediate authority_a
    valid_authority -> authority_a -> authority_b
    """
    authority = manager.get_or_create_ca("authority_b",
                                         hosts=["*.com"],
                                         certificate_authority=authority_a)
    request.addfinalizer(authority.delete_files)
    return authority


@pytest.fixture(scope="module")
def certificate_1(create_cert, valid_authority) -> Certificate:
    """
    Certificate whose chain has length 1
    valid_authority -> certificate_1
    """
    return create_cert("len_1", valid_authority)


@pytest.fixture(scope="module")
def certificate_2(create_cert, authority_a):
    """
    Certificate whose chain has length 2
    valid_authority -> authority_a -> certificate_2
    """
    return create_cert("len_2", authority_a)


@pytest.fixture(scope="module")
def certificate_3(create_cert, authority_b):
    """
    Certificate whose chain has length 3
    valid_authority -> authority_a -> authority_b -> certificate_3
    """
    return create_cert("len_3", authority_b)


@pytest.fixture(scope="module")
def chain_len3(chainify, authority_b, authority_a, valid_authority, certificate_3):
    """Client certificate chain with length of 3"""
    return chainify(certificate_3, authority_b, authority_a, valid_authority)


@pytest.fixture(scope="module")
def chain_len2(chainify, authority_a, valid_authority, certificate_2):
    """Client certificate chain with length of 2"""
    return chainify(certificate_2, authority_a, valid_authority)


@pytest.fixture(scope="module")
def chain_len1(chainify, certificate_1, valid_authority):
    """Client certificate chain with length of 2"""
    return chainify(certificate_1, valid_authority)


@pytest.fixture(scope="module", params=[
    pytest.param((1, "valid_authority", "chain_len1", 200), id="Length 1 - Depth 1"),
    pytest.param((1, "authority_a", "chain_len2", 400), id="Length 2 - Depth 1"),
    pytest.param((2, "authority_a", "chain_len2", 200), id="Length 2 - Depth 2"),
    pytest.param((2, "authority_b", "chain_len3", 400), id="Length 3 - Depth 2"),
    pytest.param((3, "authority_b", "chain_len3", 200), id="Length 3 - Depth 2"),
])
def certificates_and_code(request, staging_gateway):
    """
    Sets up gateway to the specify depth and returns configuration for service and test
    Input: Depth, Autority to be passed to Client Verification, Certificate to be used in request, Expected return code
    """
    staging_gateway.environ["APICAST_HTTPS_VERIFY_DEPTH"] = request.param[0]
    return [request.getfixturevalue(request.param[1])], request.getfixturevalue(request.param[2]), request.param[3]


def test_certificate_depth(api_client, certificates_and_code):
    """Test that TLS validation returns expected result when using client certificate with certain maximum depth"""
    _, certificate, code = certificates_and_code
    response = api_client(cert=(certificate.files["certificate"], certificate.files["key"])).get("/get")
    assert response.status_code == code
