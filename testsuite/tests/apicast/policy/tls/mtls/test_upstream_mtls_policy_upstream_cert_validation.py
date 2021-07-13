"""
Tests TLS verification of the upstream API certificate.

It uses one configuration of custom deployed httpbin (with valid certificate) and three settings of the mTLS policy:
First the ca_certificates contains a valid certificate and 200 is returned.
Second the ca_certificates contains mismatched certificates, which should fail with 502 due to APIcast
refusing to accept the other certificate.
Third the no certificates are specified in ca_certificates, in which case APIcast returns 200
"""

import pytest

from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite.capabilities import Capability
from testsuite.tests.apicast.policy.tls import embedded
from testsuite import TESTED_VERSION, rawobj # noqa # pylint: disable=unused-import


pytestmark = [
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY),
    pytest.mark.skipif("TESTED_VERSION < Version('2.11')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7099")
]


@pytest.fixture(scope="module")
def authority_and_code(valid_authority):
    """Returns authority for httpbin, the return code is not used"""
    return valid_authority, 200


@pytest.fixture(scope="module", params=[
        pytest.param(("valid_authority", 200), id="Matching authorities"),
        pytest.param(("invalid_authority", 502), id="Mismatched authorities"),
        pytest.param((None, 200), id="No provided authorities")

])
def authority_and_code_policy_settings(request):
    """Returns authority for setting the ca_certificates in the policy settings
     and return code that should be returned"""
    return request.getfixturevalue(request.param[0]) if request.param[0] is not None else None,\
        request.param[1]


@pytest.fixture(scope="module")
def policy_settings(certificate, authority_and_code_policy_settings):
    """Sets up the mTLS policy with a trusted certificates for the upstream api
    (based on the authority_and_code_policy_settings)"""
    authority, _ = authority_and_code_policy_settings

    embedded_cert = embedded(certificate.certificate, "tls.crt", "pkix-cert")
    embedded_key = embedded(certificate.key, "tls.key", "x-iwork-keynote-sffkey")

    configuration = {"certificate_type": "embedded",
                     "certificate_key_type": "embedded",
                     "certificate": embedded_cert,
                     "certificate_key": embedded_key,
                     "verify": True}

    if authority is not None:
        configuration["ca_certificates"] = [authority.certificate]

    return rawobj.PolicyConfig("upstream_mtls", configuration)


def test_mtls_request(api_client, authority_and_code_policy_settings):
    """Test that mTLS request returns correct status code"""
    _, code = authority_and_code_policy_settings
    response = api_client().get("/get")
    assert response.status_code == code
