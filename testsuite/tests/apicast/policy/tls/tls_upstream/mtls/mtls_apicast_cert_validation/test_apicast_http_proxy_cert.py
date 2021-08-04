"""
Test upstream mTLS that is set up not using any policy, but by setting environment variables
APICAST_PROXY_HTTPS_CERTIFICATE_KEY and APICAST_PROXY_HTTPS_CERTIFICATE. This does the same as upstream mTLS policy,
only globally.
"""
import pytest

from testsuite.certificates import Certificate
from testsuite.gateways import TemplateApicastOptions, TemplateApicast
from testsuite.capabilities import Capability
from testsuite.utils import blame

pytestmark = [
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-672")]


@pytest.fixture(scope="module", params=[
        pytest.param(("valid_authority", 200), id="Matching authorities"),
        pytest.param(("invalid_authority", 502), id="Mismatched authorities")
])
def authority_and_code(request):
    """
    Returns authority for httpbin and return code it should return
    """
    return request.getfixturevalue(request.param[0]), request.param[1]


@pytest.fixture(scope="module")
def staging_gateway(request, configuration, settings_block):
    """Deploy template apicast gateway."""

    options = TemplateApicastOptions(staging=True, settings_block=settings_block, configuration=configuration)
    gateway = TemplateApicast(requirements=options)

    request.addfinalizer(gateway.destroy)

    gateway.create()
    return gateway


@pytest.fixture(scope="module")
def setup_gateway(request, mount_certificate_secret, staging_gateway, certificate):
    """Sets up environment variables and volumes"""
    path = f'/var/run/secrets/{blame(request, "http_proxy_cert")}'
    mount_certificate_secret(path, certificate)

    staging_gateway.environ.set_many({
        "APICAST_PROXY_HTTPS_CERTIFICATE_KEY": f"{path}/tls.key",
        "APICAST_PROXY_HTTPS_CERTIFICATE": f"{path}/tls.crt"
    })


@pytest.fixture(scope="module")
def settings_block(request):
    """Settings block for staging gateway"""
    return {
        "deployments": {
            "staging": blame(request, "staging"),
            "production": blame(request, "production")
        }
    }


@pytest.fixture(scope="session")
def invalid_authority(request, configuration) -> Certificate:
    """To be used in tests validating server certificates"""
    certificate_authority = configuration.manager.get_or_create_ca("invalid_ca", hosts=["*.com"])
    request.addfinalizer(certificate_authority.delete_files)
    return certificate_authority


# pylint: disable=unused-argument
def test_mtls_request(api_client, authority_and_code, setup_gateway, staging_gateway):
    """Test that mtls request returns correct status code"""
    _, code = authority_and_code
    assert api_client().get("/get").status_code == code
