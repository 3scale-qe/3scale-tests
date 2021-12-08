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
from testsuite.openshift.objects import Routes
from testsuite.tests.apicast.policy.tls import embedded
from testsuite import TESTED_VERSION, rawobj # noqa # pylint: disable=unused-import
from testsuite.utils import blame

pytestmark = [
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT),
    pytest.mark.skipif("TESTED_VERSION < Version('2.11')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7099")
]


@pytest.fixture(scope="module")
def apicast_certificate(certificate):
    """
    Certificate used by APIcast sent to be validated by upstream.
    """
    return certificate


@pytest.fixture(scope="module")
def valid_upstream_hostname(superdomain):
    """
    Upstream hostname matching the upstream domain name
    """
    return "*." + superdomain.split(".", 1)[1]


@pytest.fixture(scope="module")
def invalid_upstream_hostname():
    """
    Upstream hostname NOT matching the domain name
    """
    return "mismatched_hostname"


@pytest.fixture(scope="module", params=[
        pytest.param(("valid_authority", "valid_upstream_hostname", 200), id="Matching authority"),
        pytest.param(("invalid_authority", "valid_upstream_hostname", 502), id="Mismatched authority"),
        pytest.param((None, "valid_upstream_hostname", 502), id="No provided authority",
                     marks=[pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7508")]),
        pytest.param(("valid_authority", "invalid_upstream_hostname", 502), id="Invalid upstream hostname",
                     marks=[pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-768")]),
])
def apicast_auth_httpbin_host_expected_code(request):
    """
    Returns authority for setting the ca_certificates in the policy settings at APIcast,
    hostname used by the upstream certificate and the expected return code.
    """
    return request.getfixturevalue(request.param[0]) if request.param[0] is not None else None,\
        request.getfixturevalue(request.param[1]), request.param[2]


@pytest.fixture(scope="module")
def apicast_authority(apicast_auth_httpbin_host_expected_code):
    """
    Authority of the upstream API used to validate certificates sent from APIcast
    """
    authority, _, _ = apicast_auth_httpbin_host_expected_code
    return authority


@pytest.fixture(scope="module")
def upstream_cert_hostname(apicast_auth_httpbin_host_expected_code):
    """
    Hostname of the certificate used by upstream
    """
    _, upstream_cert_hostname, _ = apicast_auth_httpbin_host_expected_code
    return upstream_cert_hostname


@pytest.fixture(scope="module")
def policy_settings(apicast_authority, apicast_certificate):
    """
    Sets up the mTLS policy with a trusted certificates for the upstream api
    (based on the authority_and_code_policy_settings)
    """
    embedded_cert = embedded(apicast_certificate.certificate, "tls.crt", "pkix-cert")
    embedded_key = embedded(apicast_certificate.key, "tls.key", "x-iwork-keynote-sffkey")

    configuration = {"certificate_type": "embedded",
                     "certificate_key_type": "embedded",
                     "certificate": embedded_cert,
                     "certificate_key": embedded_key,
                     "verify": True}

    if apicast_authority is not None:
        configuration["ca_certificates"] = [apicast_authority.certificate]

    return rawobj.PolicyConfig("upstream_mtls", configuration)


@pytest.fixture(scope="module")
def httpbin(custom_httpbin, request):
    """
    Deploys httpbin with mTLS enabled with routing by routes
    """
    return custom_httpbin(blame(request, "httpbin-mtls"), Routes.Types.PASSTHROUGH)


def test_mtls_upstream_cert_validation(api_client, apicast_auth_httpbin_host_expected_code):
    """
    Test that APIcast correctly validates the certificate sent by the upstream
    """
    _, _, expected_response_code = apicast_auth_httpbin_host_expected_code
    response = api_client().get("/get")

    assert response.status_code == expected_response_code
