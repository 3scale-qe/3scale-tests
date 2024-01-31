"""
Configuration for tests making use of an upstream supporting TLS
"""

from urllib.parse import urlparse

import pytest

import importlib_resources as resources

from testsuite import rawobj
from testsuite.certificates import Certificate
from testsuite.utils import blame


@pytest.fixture(scope="module")
def upstream_authority(valid_authority):
    """
    Authority of the upstream API used to validate certificates sent from APIcast.
    May be overwritten to configure different test cases.
    """
    return valid_authority


@pytest.fixture(scope="module")
def upstream_cert_hostname(staging_gateway):
    """
    Hostname of the upstream certificate sent to be validated by APIcast
    May be overwritten to configure different test cases
    """
    hostname = urlparse(staging_gateway.openshift.api_url).hostname
    return "*.apps" + hostname.split(".", 1)[1]


@pytest.fixture(scope="module")
def upstream_certificate(request, manager, valid_authority, upstream_cert_hostname, testconfig) -> Certificate:
    """
    Certificate sent from upstream (httpbin) to be validated by APIcast
    """
    label = "httpbin_" + upstream_cert_hostname
    cert = manager.get_or_create(
        label, common_name=upstream_cert_hostname, hosts=[upstream_cert_hostname], certificate_authority=valid_authority
    )

    if not testconfig["skip_cleanup"]:
        request.addfinalizer(cert.delete_files)
    return cert


@pytest.fixture(scope="session")
def invalid_host_authority(request, manager, testconfig) -> Certificate:
    """To be used in tests validating server certificates"""
    certificate_authority = manager.get_or_create_ca("invalid_host_ca", hosts=["*.com"])
    if not testconfig["skip_cleanup"]:
        request.addfinalizer(certificate_authority.delete_files)
    return certificate_authority


@pytest.fixture(scope="session")
def invalid_host_certificate(invalid_host_authority, create_cert) -> Certificate:
    """Valid certificate for entire 3scale superdomain"""
    return create_cert("invalid_host", invalid_host_authority)


@pytest.fixture(scope="module")
def httpbin(custom_httpbin, request):
    """
    Deploys httpbin with mTLS enabled
    """
    return custom_httpbin(blame(request, "httpbin-mtls"))


# pylint: disable=too-many-arguments
@pytest.fixture(scope="module")
def custom_httpbin(staging_gateway, request, upstream_certificate, upstream_authority, testconfig):
    """
    Deploys httpbin with a custom name with mTLS enabled.
    If tls_route_type is set, creates routes for the backend with given TLS type
    and returns the public route of the backend.
    """
    httpbin_image = testconfig["fixtures"]["custom_httpbin"]["image"]

    def _httpbin(name, tls_route_type=None):
        path = resources.files("testsuite.resources.tls").joinpath("httpbin_go.yaml")
        name = blame(request, name)
        parameters = {
            "NAME": name,
            "CERTIFICATE": upstream_certificate.certificate,
            "CERTIFICATE_KEY": upstream_certificate.key,
            "CA_CERTIFICATE": upstream_authority.certificate,
            "IMAGE": httpbin_image,
        }

        if not testconfig["skip_cleanup"]:
            request.addfinalizer(lambda: staging_gateway.openshift.delete_template(path, parameters))
        staging_gateway.openshift.new_app(path, parameters)
        # pylint: disable=protected-access
        staging_gateway.openshift.deployment(f"dc/{name}").wait_for()

        if tls_route_type is not None:
            if not testconfig["skip_cleanup"]:
                request.addfinalizer(lambda: staging_gateway.openshift.delete("route", name))
            staging_gateway.openshift.routes.create(name, tls_route_type, service=name)
            routes = staging_gateway.openshift.routes[name]
            return f"https://{routes['spec']['host']}:443"

        return f"https://{name}:8443"

    return _httpbin


@pytest.fixture(scope="module")
def service_proxy_settings(httpbin):
    """Dict of proxy settings to be used when service created"""
    return rawobj.Proxy(httpbin)
