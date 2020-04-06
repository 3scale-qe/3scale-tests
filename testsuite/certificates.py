"""Collection of classes for working with different ssl certificate tools."""
import abc
import collections
import tempfile
import os
from typing import List

from cfssl import CFSSL

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


class CFSSLCertificate(Certificate):  # pylint: disable=too-few-public-methods
    """CFSSL Certificate implementation."""

    def __init__(self, host: str, port: int, ssl: bool = False,
                 verify_cert: bool = False):
        self.cfssl = CFSSL(host, port, ssl=ssl, verify_cert=verify_cert)

    def create(self, common_name: str, names: List[str] = None,
               hosts: List[str] = None) -> CreateCertificateResponse:
        new_key = self.cfssl.new_key(hosts, names, common_name=common_name)

        signed_certificate = self.cfssl.sign(new_key["certificate_request"], hosts=hosts)

        return CreateCertificateResponse(
            certificate=signed_certificate,
            key=new_key["private_key"])


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


class TmpCertificateStore(CertificateStore):
    """Temporary file implementation."""

    def __init__(self):
        self.tempdir = tempfile.gettempdir()
        self.path = f"{self.tempdir}/certs"
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def _read(self, name: str, ext: str) -> str:
        with open(f"{self.path}/{name}.{ext}", "r") as file:
            content = file.read()
        return content

    def _persist(self, name: str, ext: str, content: str):
        with open(f"{self.path}/{name}.{ext}", "w") as file:
            file.write(content)

    def save(self, name: str, cert: str, key: str):
        self._persist(name, "crt", cert)
        self._persist(name, "key", key)

    def get(self, name: str) -> GetCertificateResponse:
        return GetCertificateResponse(
            certificate=self._read(name, "crt"),
            key=self._read(name, "key"),
            certificate_path=f"{self.path}/{name}.crt",
            key_path=f"{self.path}/{name}.key",
        )


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
