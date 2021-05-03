"""Configuration for mTLS tests"""
import pytest

import importlib_resources as resources

from testsuite import rawobj
from testsuite.certificates import Certificate
from testsuite.utils import blame


@pytest.fixture(scope="module", params=[
        pytest.param(("valid_authority", 200), id="Matching authorities"),
        pytest.param(("invalid_authority", 502), id="Mismatched authorities")
])
def authority_and_code(request):
    """Returns authority for httpbin and return code it should return"""
    return request.getfixturevalue(request.param[0]), request.param[1]


@pytest.fixture(scope="module")
def httpbin_certificate(request, authority_and_code, configuration) -> Certificate:
    """Certificate for httpbin"""
    authority, _ = authority_and_code
    host = "*." + configuration.superdomain
    cert = configuration.manager.get_or_create("httpbin",
                                               common_name=host,
                                               hosts=[host],
                                               certificate_authority=authority)

    request.addfinalizer(cert.delete_files)
    return cert


@pytest.fixture(scope="module")
def httpbin(custom_httpbin, request):
    """
    Deploys httpbin with mTLS enabled
    """
    return custom_httpbin(blame(request, "httpbin-mtls"))


@pytest.fixture(scope="module")
def custom_httpbin(staging_gateway, request, httpbin_certificate, authority_and_code, openshift):
    """
    Deploys httpbin with a custom name with mTLS enabled.
    If tls_route_type is set, creates routes for the backend with given TLS type
    and returns the public route of the backend.
    """
    openshift = openshift()

    def _httpbin(name, tls_route_type=None):
        path = resources.files('testsuite.resources.tls').joinpath('httpbin_go.yaml')
        authority, _ = authority_and_code
        name = blame(request, name)
        parameters = {
            "NAME": name,
            "CERTIFICATE": httpbin_certificate.certificate,
            "CERTIFICATE_KEY": httpbin_certificate.key,
            "CA_CERTIFICATE": authority.certificate,
        }

        def _delete():
            staging_gateway.openshift.delete_app(name, "all")
        request.addfinalizer(_delete)

        staging_gateway.openshift.new_app(path, parameters)
        # pylint: disable=protected-access
        staging_gateway.openshift._wait_for_deployment(name)

        if tls_route_type is not None:
            openshift.routes.create(name, tls_route_type, service=name)
            routes = openshift.routes[name]
            return f"https://{routes['spec']['host']}:443"

        return f"https://{name}:8443"

    return _httpbin


@pytest.fixture(scope="module")
def service_proxy_settings(httpbin):
    """Dict of proxy settings to be used when service created"""
    return rawobj.Proxy(httpbin)
