"""Module for setting up test that require TLS gateway and/or certificates"""

from weakget import weakget
import pytest

from testsuite.certificates import Certificate, CertificateManager
from testsuite.certificates.cfssl.cli import CFSSLProviderCLI
from testsuite.certificates.stores import InMemoryCertificateStore
from testsuite.gateways import gateway
from testsuite.gateways.apicast.tls import TLSApicast
from testsuite.openshift.objects import SecretKinds
from testsuite.utils import blame, warn_and_skip


@pytest.fixture(scope="module", autouse=True)
def require_openshift(testconfig):
    """These tests require openshift available"""
    if not weakget(testconfig)["openshift"]["servers"]["default"] % False:
        warn_and_skip("All from tls skipped due to missing openshift")


@pytest.fixture(scope="session")
def manager(testconfig):
    """Certificate Manager"""
    provider = CFSSLProviderCLI(binary=testconfig["cfssl"]["binary"])
    store = InMemoryCertificateStore()
    return CertificateManager(provider, provider, store)


@pytest.fixture(scope="session")
def superdomain(testconfig):
    """3scale superdomain"""
    return testconfig["threescale"]["superdomain"]


@pytest.fixture(scope="session")
def server_authority(request, superdomain, manager):
    """CA Authority to be used in the gateway"""
    wildcard_domain = "*." + superdomain
    authority = manager.get_or_create_ca("server-ca", hosts=[wildcard_domain])
    request.addfinalizer(authority.delete_files)
    return authority


# pylint: disable=too-many-arguments
@pytest.fixture(scope="module")
def staging_gateway(request, server_authority, superdomain, manager, gateway_options, gateway_environment):
    """Deploy tls apicast gateway. We need APIcast listening on https port"""
    kwargs = {
        "name": blame(request, "tls-gw"),
        "manager": manager,
        "server_authority": server_authority,
        "superdomain": superdomain,
    }
    kwargs.update(gateway_options)
    gw = gateway(kind=TLSApicast, staging=True, **kwargs)

    request.addfinalizer(gw.destroy)
    gw.create()

    if len(gateway_environment) > 0:
        gw.environ.set_many(gateway_environment)

    return gw


@pytest.fixture(scope="session")
def create_cert(request, superdomain, manager):
    """Creates certificate that is valid for entire 3scale subdomain"""
    host = "*." + superdomain

    def _create(name: str, certificate_authority: Certificate) -> Certificate:
        cert = manager.get_or_create(name, common_name=host, hosts=[host], certificate_authority=certificate_authority)

        request.addfinalizer(cert.delete_files)
        return cert

    return _create


@pytest.fixture(scope="session")
def chainify(request):
    """Creates chain from certificate and his certificate authorities"""

    def _chain(certificate: Certificate, *authorities: Certificate) -> Certificate:
        entire_chain = [certificate]
        entire_chain.extend(authorities)
        chain = Certificate(certificate="".join(cert.certificate for cert in entire_chain), key=certificate.key)
        request.addfinalizer(chain.delete_files)
        return chain

    return _chain


@pytest.fixture(scope="session")
def valid_authority(request, manager) -> Certificate:
    """To be used in tests validating server certificates"""
    certificate_authority = manager.get_or_create_ca("valid_ca", hosts=["*.com"])
    request.addfinalizer(certificate_authority.delete_files)
    return certificate_authority


@pytest.fixture(scope="session")
def certificate(valid_authority, create_cert) -> Certificate:
    """Valid certificate for entire 3scale superdomain"""
    return create_cert("valid", valid_authority)


@pytest.fixture(scope="module")
def invalid_authority(staging_gateway):
    """Authority for testing negative case, same as the CA used in gateway"""
    return staging_gateway.server_authority


@pytest.fixture(scope="module")
def invalid_certificate(invalid_authority, create_cert) -> Certificate:
    """Valid certificate for entire 3scale superdomain"""
    return create_cert("invalid", invalid_authority)


@pytest.fixture(scope="module")
def mount_certificate_secret(request, staging_gateway):
    """Mount volume from TLS secret on staging gateway."""

    def _mount(mount_path, certificate):
        secret_name = blame(request, "tls")

        def turn_down():
            staging_gateway.openshift.delete("secret", secret_name)

        request.addfinalizer(turn_down)

        staging_gateway.openshift.secrets.create(secret_name, SecretKinds.TLS, certificate=certificate)
        staging_gateway.deployment.add_volume(secret_name, mount_path, secret_name)

    return _mount


# pylint: disable=too-many-arguments
@pytest.fixture(scope="module")
def service(request, backends_mapping, custom_service, service_proxy_settings, lifecycle_hooks, policy_settings):
    """Preconfigured service, which is created for each policy settings, which are often parametrized in this module"""
    service = custom_service(
        {"name": blame(request, "svc")}, service_proxy_settings, backends_mapping, hooks=lifecycle_hooks
    )
    if policy_settings:
        service.proxy.list().policies.append(policy_settings)
    return service


@pytest.fixture(scope="module")
def gateway_options():
    """Additional options to pass to staging gateway constructor"""
    return {}


@pytest.fixture(scope="module")
def gateway_environment():
    """Allows setting environment for tls tests"""
    return {}
