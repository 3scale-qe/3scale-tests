"""
Tests upstream mTLS policy with TLS gateway, which enables mTLS between APIcast and upstream api (httpbin)

It uses two configuration of custom deployed Httpbin:
First with matching certificates and authorities, which should succeed with 200
Second with mismatched certificates, which should fail with 502 due to httpbin refusing to accept the other certificate

It also tests both embedded and path type policies, so in total it runs 4 combinations of tests
"""
import pytest

from testsuite import rawobj
from testsuite.capabilities import Capability
from testsuite.tests.apicast.policy.tls import embedded
from testsuite.utils import blame

pytestmark = [
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY)
]


@pytest.fixture(scope="module")
def embedded_policy_settings(certificate):
    """Sets up the embedded upstream mTLS policy"""
    embedded_cert = embedded(certificate.certificate, "tls.crt", "pkix-cert")
    embedded_key = embedded(certificate.key, "tls.key", "x-iwork-keynote-sffkey")
    return rawobj.PolicyConfig("upstream_mtls", {"certificate_type": "embedded",
                                                 "certificate_key_type": "embedded",
                                                 "certificate": embedded_cert,
                                                 "certificate_key": embedded_key})


@pytest.fixture(scope="module")
def path_policy_settings(request, certificate, mount_certificate_secret):
    """Sets up upstream mTLS policy with local certificates"""
    path = f'/var/run/secrets/{blame(request, "mtls")}'
    mount_certificate_secret(path, certificate)
    return rawobj.PolicyConfig("upstream_mtls", {"certificate_type": "path",
                                                 "certificate_key_type": "path",
                                                 "certificate": f"{path}/tls.crt",
                                                 "certificate_key": f"{path}/tls.key"})


@pytest.fixture(scope="module", params=(
        pytest.param("embedded_policy_settings", id="Embedded"),
        pytest.param("path_policy_settings", id="Path")
))
def policy_settings(request):
    """Paramterized policy settings for upstream mTLS policy"""
    return request.getfixturevalue(request.param)


def test_mtls_request(api_client, authority_and_code):
    """Test that mtls request returns correct status code"""
    _, code = authority_and_code
    assert api_client().get("/get").status_code == code
