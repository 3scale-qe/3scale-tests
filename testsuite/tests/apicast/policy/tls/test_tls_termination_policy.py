"""Test for TLS Termination Policy.
This policy instructs APIcast to use specific certificate for communicating with client.
Tests both embedded and path type"""

import pytest
import requests

from testsuite import rawobj
from testsuite.capabilities import Capability
from testsuite.tests.apicast.policy.tls import embedded
from testsuite.utils import blame

pytestmark = [
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT),
    pytest.mark.issue("https://issues.jboss.org/browse/THREESCALE-2898"),
]


@pytest.fixture(scope="module")
def embedded_policy_settings(certificate):
    """Sets up the embedded TLS termination policy"""
    return rawobj.PolicyConfig(
        "tls",
        {
            "certificates": [
                {
                    "certificate": embedded(certificate.certificate, "tls.crt", "pkix-cert"),
                    "certificate_key": embedded(certificate.key, "tls.key", "x-iwork-keynote-sffkey"),
                }
            ]
        },
    )


@pytest.fixture(scope="module")
def path_policy_settings(request, certificate, mount_certificate_secret):
    """Sets up TLS termination policy with local certificates"""
    path = f'/var/run/secrets/{blame(request, "tls-term")}'
    mount_certificate_secret(path, certificate)
    return rawobj.PolicyConfig(
        "tls", {"certificates": [{"certificate_path": f"{path}/tls.crt", "certificate_key_path": f"{path}/tls.key"}]}
    )


@pytest.fixture(
    scope="module",
    params=(
        pytest.param("embedded_policy_settings", id="Embedded"),
        pytest.param("path_policy_settings", id="Path", marks=pytest.mark.required_capabilities(Capability.OCP3)),
    ),
)
def policy_settings(request):
    """TLS termination policy settings"""
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="function")
def client(api_client):
    """Returns HttpClient instance with retrying feature skipped."""
    api_client = api_client(disable_retry_status_list={503, 404})
    # This won't work with Httpx but will save us about 10 mins for this test alone
    api_client.session = requests.Session()
    return api_client


def test_get_should_return_ok(api_client, valid_authority):
    """Test tls termination policy with embedded type configuration."""
    assert api_client(verify=valid_authority.files["certificate"]).get("/get").status_code == 200


def test_get_without_certs_should_fail(client):
    """Test tls termination policy with embedded type configuration."""

    with pytest.raises(Exception, match="certificate verify failed: unable to get local issuer certificate"):
        client.get("/get")
