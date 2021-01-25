"""Module for setting up test that require TLS gateway and/or certificates"""
import pytest

from testsuite.certificates import Certificate
from testsuite.gateways import TLSApicastOptions, TLSApicast
from testsuite.utils import blame


@pytest.fixture(scope="module")
def staging_gateway(request, configuration):
    """Deploy tls apicast gateway. We need APIcast listening on https port"""
    settings_block = {
        "deployments": {
            "staging": blame(request, "tls-apicast"),
            "production": blame(request, "tls-apicast"),
        }
    }
    options = TLSApicastOptions(staging=True, settings_block=settings_block, configuration=configuration)
    gateway = TLSApicast(requirements=options)

    request.addfinalizer(gateway.destroy)
    gateway.create()

    return gateway


@pytest.fixture(scope="session")
def valid_authority(request, configuration) -> Certificate:
    """To be used in tests validating server certificates"""
    certificate_authority = configuration.manager.get_or_create_ca("valid_ca", hosts=["*.com"])
    request.addfinalizer(certificate_authority.delete_files)
    return certificate_authority


@pytest.fixture(scope="session")
def certificate(request, valid_authority, configuration) -> Certificate:
    """Valid certificate for entire 3scale superdomain"""
    host = "*." + configuration.superdomain
    cert = configuration.manager.get_or_create("valid",
                                               common_name=host,
                                               hosts=[host],
                                               certificate_authority=valid_authority)

    request.addfinalizer(cert.delete_files)
    return cert


@pytest.fixture(scope="module")
def invalid_authority(staging_gateway):
    """Authority for testing negative case, same as the CA used in gateway"""
    return staging_gateway.server_authority


@pytest.fixture(scope="module")
def invalid_certificate(request, invalid_authority, configuration) -> Certificate:
    """Valid certificate for entire 3scale superdomain"""
    host = "*." + configuration.superdomain
    cert = configuration.manager.get_or_create("invalid",
                                               common_name=host,
                                               hosts=[host],
                                               certificate_authority=invalid_authority)

    request.addfinalizer(cert.delete_files)
    return cert


@pytest.fixture(scope="module")
def mount_certificate_secret(request, staging_gateway):
    """Mount volume from TLS secret on staging gateway."""

    def _mount(mount_path, certificate):
        secret_name = blame(request, "tls-term")
        resource = {
            "kind": "Secret",
            "apiVersion": "v1",
            "metadata": {
                "name": secret_name,
            },
            "stringData": {
                "tls.crt": certificate.certificate,
                "tls.key": certificate.key,
            }
        }

        def turn_down():
            staging_gateway.openshift.delete("secret", secret_name)

        request.addfinalizer(turn_down)

        staging_gateway.openshift.apply(resource)
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
