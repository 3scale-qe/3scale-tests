"""Tests for TLS validation policy.
This policy checks client certificates against whitelist of certificates or CAs
This tests check how TLS validation policy acts when multiple certs are provided"""
import pytest

from testsuite.capabilities import Capability

pytestmark = pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT)


@pytest.fixture(scope="module", params=[
    pytest.param(("all_valid", 200), id="all_certs_valid"),
    pytest.param(("no_valid", 400), id="no_valid_certs"),
    pytest.param(("some_valid1", 200), id="some_certs_valid1"),
    pytest.param(("some_valid2", 200), id="some_certs_valid2"),
    pytest.param(("empty", 400), id="empty_chain"),
])
def certificates_and_code(request, certificate):
    """List of certificates and their respective expected return codes"""
    return request.getfixturevalue(request.param[0]), certificate, request.param[1]


@pytest.fixture(scope="module")
def all_valid(certificate, valid_authority):
    """Chain where both of the two certificates provided is valid (will pass the test)"""
    return [certificate, valid_authority]


@pytest.fixture(scope="module")
def empty():
    """Chain where the policy is empty"""
    return []


@pytest.fixture(scope="module")
def no_valid(invalid_certificate, invalid_authority):
    """Chain where none of the two certificates provided is valid (will pass the test)"""
    return [invalid_authority, invalid_certificate]


@pytest.fixture(scope="module")
def some_valid1(certificate, invalid_authority):
    """Chain where one of the two certificates provided is valid (will pass the test)"""
    return [certificate, invalid_authority]


@pytest.fixture(scope="module")
def some_valid2(invalid_certificate, valid_authority):
    """Chain where one of the two certificates provided is valid (will pass the test)"""
    return [invalid_certificate, valid_authority]


def test_tls_validation(api_client, certificates_and_code):
    """Test that TLS validation returns expected result when using client certificate"""
    _, certificate, code = certificates_and_code

    client = api_client(cert=(certificate.files["certificate"], certificate.files["key"]))
    response = client.get("/get")

    assert response.status_code == code
