
"""Collection of classes for working with different ssl certificate tools."""
import abc
import collections
from typing import List
from urllib.parse import urlparse

CreateCertificateResponse = collections.namedtuple("CreateCerficateResponse", ["certificate", "key"])
GetCertificateResponse = collections.namedtuple("GetCertificateResponse",
                                                ["certificate", "key", "certificate_path", "key_path"])


class Certificate(abc.ABC):  # pylint: disable=too-few-public-methods
    """Certificate abstract class."""

    @abc.abstractmethod
    def create(self, common_name: str, names: List[str] = None,
               hosts: List[str] = None) -> CreateCertificateResponse:
        """Create a ssl certificate.
        Args:
            :param common_name: The fully qualified domain name for
                the server. This must be an exact match.
            :param names: Subject Information to be added to the request.
            :param hosts: Hosts to be added to the request.
        """


class CertificateStore(abc.ABC):
    """Provide persistency for certificates."""

    @abc.abstractmethod
    def save(self, name: str, cert: str, key: str):
        """Persist PEM-like certificate and key.
        Args:
            :param name: To label the cert and key.
            :param cert: PEM-like certificate.
            :param key: certificate key.
        """

    @abc.abstractmethod
    def get(self, name: str) -> GetCertificateResponse:
        """Get PEM-like certificate and key.
        Args:
            :param name: name of certificate and key.
        """


class CertificateManager:  # pylint: disable=too-few-public-methods
    """Certificate Manager.

    Provides a common interface to many certificate and storages types.
    """

    def __init__(self, certificate: Certificate, store: CertificateStore):
        self.certificate = certificate
        self.store = store

    def create(self, label: str, *args, **kwargs) -> CreateCertificateResponse:
        """Create a new certificate.
        Args:
            :param label: a identifier to the certificate and key.
        """
        certificate = self.certificate.create(*args, **kwargs)
        self.store.save(label, certificate.certificate, certificate.key)
        return certificate


class SSLCertificate:
    """Class for working with certificate stuff for TLSAPicast."""

    def __init__(self, endpoint: str, cert_manager: CertificateManager, cert_store: CertificateStore):
        self.endpoint = endpoint
        self._cert_manager = cert_manager
        self._cert_store = cert_store

    @property
    def _hostname(self):
        """Returns wildcard endpoint."""
        return urlparse(self.endpoint % "*").hostname

    @property
    def _csr_names(self):
        """Returns data for CSR's names field."""
        return {
            "O": self._hostname,
            "OU": "IT",
            "L": "San Francisco",
            "ST": "California",
            "C": "US",
        }

    def create(self, label: str) -> CreateCertificateResponse:
        """Create a new ssl certificate.
        Args:
            :param label: Identifier for the certificate.
        Returns:
            certificate: Certificate PEM-like.
            private_key: Key PEM-like.
        """
        return self._cert_manager.create(label, self._hostname, hosts=[self._hostname],
                                         names=[self._csr_names])

    def get(self, label: str) -> GetCertificateResponse:
        """Get existent certificate.
        Args:
            :param label: Identifier for the certificate.
        Returns:
            certificate: Certificate PEM-like.
            private_key: Key PEM-like.
        """
        return self._cert_store.get(label)
