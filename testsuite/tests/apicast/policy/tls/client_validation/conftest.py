"""Conftest for TLS validation tests"""

import pytest

from testsuite import rawobj


@pytest.fixture(scope="module")
def certificates_and_code():
    """Returns list of certificates or certificate authorities to pass into the policy and resulting return code
    Meant to be overriden in individual tests
    Return type: Tuple[List[Certificate], Certificate, int]:
    """
    return [], None, None


@pytest.fixture(scope="module")
def policy_settings(certificates_and_code):
    """TLS validation policy settings"""
    certificates, _, _ = certificates_and_code
    config = []
    for certificate in certificates:
        config.append({"pem_certificate": certificate.certificate})
    return rawobj.PolicyConfig("tls_validation", {"whitelist": config})
