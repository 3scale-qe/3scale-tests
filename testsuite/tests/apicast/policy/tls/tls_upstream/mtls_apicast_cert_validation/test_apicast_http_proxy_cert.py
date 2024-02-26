"""
Test upstream mTLS that is set up not using any policy, but by setting environment variables
APICAST_PROXY_HTTPS_CERTIFICATE_KEY and APICAST_PROXY_HTTPS_CERTIFICATE. This does the same as upstream mTLS policy,
only globally.
"""

import pytest

from testsuite.certificates import Certificate
from testsuite.capabilities import Capability
from testsuite.gateways import gateway
from testsuite.gateways.apicast.template import TemplateApicast
from testsuite.utils import blame

pytestmark = [
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-672"),
]


@pytest.fixture(
    scope="module",
    params=[
        pytest.param(("valid_authority", 200), id="Matching authorities"),
        pytest.param(("invalid_authority", 502), id="Mismatched authorities"),
    ],
)
def authority_and_code(request):
    """
    Returns authority for httpbin and return code it should return
    """
    return request.getfixturevalue(request.param[0]), request.param[1]


@pytest.fixture(scope="module")
def staging_gateway(request, testconfig):
    """Deploy self-managed template based apicast gateway."""
    gw = gateway(kind=TemplateApicast, staging=True, name=blame(request, "gw"))
    if not testconfig["skip_cleanup"]:
        request.addfinalizer(gw.destroy)
    gw.create()

    return gw


@pytest.fixture(scope="module")
def setup_gateway(request, mount_certificate_secret, staging_gateway, certificate):
    """Sets up environment variables and volumes"""
    path = f'/var/run/secrets/{blame(request, "http_proxy_cert")}'
    mount_certificate_secret(path, certificate)

    staging_gateway.environ.set_many(
        {"APICAST_PROXY_HTTPS_CERTIFICATE_KEY": f"{path}/tls.key", "APICAST_PROXY_HTTPS_CERTIFICATE": f"{path}/tls.crt"}
    )
    return staging_gateway


@pytest.fixture(scope="session")
def invalid_authority(request, manager, testconfig) -> Certificate:
    """To be used in tests validating server certificates"""
    certificate_authority = manager.get_or_create_ca("invalid_ca", hosts=["*.com"])
    if not testconfig["skip_cleanup"]:
        request.addfinalizer(certificate_authority.delete_files)
    return certificate_authority


# pylint: disable=unused-argument
def test_mtls_request(api_client, authority_and_code, setup_gateway, staging_gateway):
    """Test that mtls request returns correct status code"""
    _, code = authority_and_code
    assert api_client().get("/get").status_code == code
