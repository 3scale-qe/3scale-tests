"""Tests for TLS validation policy.
This policy checks client certificates against whitelist of certificates or CAs"""
import pytest

from testsuite.capabilities import Capability

pytestmark = pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT)


@pytest.fixture(
    scope="module",
    params=[
        pytest.param(("certificate", 200), id="certificate"),
        pytest.param(("valid_authority", 200), id="valid_authority"),
        pytest.param(("invalid_authority", 400), id="invalid_authority"),
        pytest.param(("invalid_certificate", 400), id="invalid_certificate"),
    ],
)
def certificates_and_code(request, certificate):
    """List of certificates and their respective expected return codes"""
    return [request.getfixturevalue(request.param[0])], certificate, request.param[1]


def test_tls_validation(api_client, certificates_and_code):
    """Test that TLS validation returns expected result when using client certificate"""
    _, certificate, code = certificates_and_code
    response = api_client(cert=(certificate.files["certificate"], certificate.files["key"])).get("/get")
    assert response.status_code == code


def test_tls_validation_no_cert(api_client):
    """Test that TLS validation with no client certificate"""
    response = api_client().get("/get")
    assert response.status_code == 400
