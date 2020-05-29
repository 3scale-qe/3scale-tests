"""Fixtures for TLS-related policies."""
from urllib.parse import urlparse

import pytest

from testsuite.certificates import SSLCertificate


@pytest.fixture(scope="module")
def ssl_certificate_hostname(private_base_url):
    """Return hostname to be used on ssl certificate creation."""
    return urlparse(private_base_url("httpbin")).hostname


@pytest.fixture(scope="module")
def ssl_certificate(ssl_certificate_hostname, configuration):
    """Returns a certificates.SSLCertificate instance."""
    return SSLCertificate(ssl_certificate_hostname,
                          configuration.manager,
                          configuration.certificate_store)


@pytest.fixture(scope="module")
def mtls_cert_and_key(configuration):
    """Returns SSL certificate and key from configured project.

    SSL certificate and key should be the same as the ones set to the mtls upstream api.
    """
    oclient = configuration.openshift(project="mtls-certificates")
    try:
        secret = oclient.secrets["mtls-certificates"]
    except KeyError as err:
        raise ValueError("`mtls-certificates` tls secret must be defined in configured namespace.") from err

    cert = secret["tls.crt"].decode("ascii")
    key = secret["tls.key"].decode("ascii")

    return cert, key
