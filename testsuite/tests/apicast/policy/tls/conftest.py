"""Module for setting up test that require TLS gateway and/or certificates"""

from weakget import weakget
import pytest

from testsuite.certificates import Certificate
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
def server_authority(request, configuration):
    """CA Authority to be used in the gateway"""
    wildcard_domain = "*." + configuration.superdomain
    authority = configuration.manager.get_or_create_ca("server-ca",
                                                       hosts=[wildcard_domain])
    request.addfinalizer(authority.delete_files)
    return authority


@pytest.fixture(scope="module")
def staging_gateway(request, testconfig, server_authority, configuration):
    """Deploy tls apicast gateway. We need APIcast listening on https port"""
    kwargs = dict(
        name=blame(request, "tls-gw"),
        manager=configuration.manager,
        server_authority=server_authority,
        superdomain=configuration.superdomain,
        **testconfig["threescale"]["gateway"]["TemplateApicast"],
    )
    gw = gateway(kind=TLSApicast, staging=True, **kwargs)

    request.addfinalizer(gw.destroy)
    gw.create()
    return gw


@pytest.fixture(scope="session")
def create_cert(request, configuration):
    """Creates certificate that is valid for entire 3scale subdomain"""
    host = "*." + configuration.superdomain

    def _create(name: str, certificate_authority: Certificate) -> Certificate:
        cert = configuration.manager.get_or_create(name,
                                                   common_name=host,
                                                   hosts=[host],
                                                   certificate_authority=certificate_authority)

        request.addfinalizer(cert.delete_files)
        return cert
    return _create


@pytest.fixture(scope="session")
def chainify(request):
    """Creates chain from certificate and his certificate authorities"""
    def _chain(certificate: Certificate, *authorities: Certificate) -> Certificate:
        entire_chain = [certificate]
        entire_chain.extend(authorities)
        chain = Certificate(certificate="".join(cert.certificate for cert in entire_chain),
                            key=certificate.key)
        request.addfinalizer(chain.delete_files)
        return chain
    return _chain


@pytest.fixture(scope="session")
def valid_authority(request, configuration) -> Certificate:
    """To be used in tests validating server certificates"""
    certificate_authority = configuration.manager.get_or_create_ca("valid_ca", hosts=["*.com"])
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
        staging_gateway.openshift.add_volume(staging_gateway.deployment, secret_name,
                                             mount_path, secret_name)
    return _mount


# pylint: disable=too-many-arguments
@pytest.fixture(scope="module")
def service(request, backends_mapping, custom_service,
            service_proxy_settings, lifecycle_hooks, policy_settings):
    """Preconfigured service, which is created for each policy settings, which are often parametrized in this module"""
    service = custom_service({"name": blame(request, "svc")}, service_proxy_settings, backends_mapping,
                             hooks=lifecycle_hooks)
    if policy_settings:
        service.proxy.list().policies.append(policy_settings)
    return service
