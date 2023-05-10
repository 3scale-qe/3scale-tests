"""Collection of classes for working with different ssl certificate tools."""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict

from testsuite.certificates.persist import TmpFilePersist

# Type alias for Names field in certification csrs
CertificateNames = List[Dict[str, str]]


class Certificate(TmpFilePersist):
    """Class representing a Certificate or a CertificateAuthority with private key and certificate"""

    def __init__(self, key, certificate) -> None:
        super().__init__()
        self.key = key
        self.certificate = certificate

    def persist(self):
        return self._persist(key=self.key, certificate=self.certificate)


class UnsignedKey(TmpFilePersist):
    """Representing generated key that hasn't been signed yet"""

    def __init__(self, key, csr) -> None:
        super().__init__()
        self.key = key
        self.csr = csr

    def persist(self):
        return self._persist(key=self.key, csr=self.csr)


class CertificateStore(ABC):
    """Provide persistence for certificates across different runs."""

    @abstractmethod
    def __contains__(self, key: str):
        """Checks if the certificate is stored in the code
        Args:
            :param key: name of the certificate.
        """

    @abstractmethod
    def __setitem__(self, key: str, value: Certificate):
        """Persist PEM-like certificate and key.
        Args:
            :param key: label of the certificate.
            :param value: Certificate to be saved
        """

    @abstractmethod
    def __getitem__(self, key: str):
        """Get PEM-like certificate and key.
        Args:
            :param key: label of certificate.
        """


# pylint: disable=too-few-public-methods
class SigningProvider(ABC):
    """Provider key signing capabilities"""

    @abstractmethod
    def sign(self, key: UnsignedKey, certificate_authority: Optional[Certificate] = None) -> Certificate:
        """Signs the generated key, returns final certificate.
        Args:
            :param key: Key to be signed
            :param certificate_authority:  Optional argument to specify which ca to use for signing
        """

    @abstractmethod
    def sign_intermediate_ca(self, key: UnsignedKey, certificate_authority: Certificate) -> Certificate:
        """Signs generate key with root certificate authority in order to create intermediate authority.
        Args:
            :param key: Key to be signed
            :param certificate_authority: Ca to be used for signing
        """


class KeyProvider(ABC):
    """Class that can generate keys to be used in certificates"""

    @abstractmethod
    def generate_key(
        self, common_name: str, names: Optional[List[Dict[str, str]]] = None, hosts: Optional[List[str]] = None
    ) -> UnsignedKey:
        """Create a new unsigned key.
        Args:
            :param common_name: The fully qualified domain name for
                the server. This must be an exact match.
            :param names: Subject Information to be added to the request.
            :param hosts: Hosts to be added to the request.
        """

    @abstractmethod
    def generate_ca(
        self,
        common_name: str,
        names: List[Dict[str, str]],
        hosts: List[str],
    ) -> Tuple[Certificate, UnsignedKey]:
        """Creates new CA key, returns both self signed certificate and Unsigned key with CSR
         if we want to make it a intermediate CA
        Args:
            :param common_name: Name of the Certificate authority
            :param names: Subject Information to be added to the request.
            :param hosts: Hosts to be added to the request.
        """


class CertificateManager:
    """Certificate Manager.

    Provides a common interface to many certificate and storages types.
    Certificate store is only used for final certificates, not keys
    Certificate Authority and Certificates share the same namespace in storage
    """

    # Default names for the Names field in the csrs
    DEFAULT_NAMES = [
        {
            "O": "Red Hat Inc.",
            "OU": "IT",
            "L": "San Francisco",
            "ST": "California",
            "C": "US",
        }
    ]

    def __init__(self, key_provider: KeyProvider, sign_provider: SigningProvider, store: CertificateStore):
        self.key_provider = key_provider
        self.sign_provider = sign_provider
        self.store = store

    # pylint: disable=too-many-arguments
    def create(
        self,
        label: str,
        common_name: str,
        hosts: List[str],
        names: Optional[List[Dict[str, str]]] = None,
        certificate_authority: Optional[Certificate] = None,
    ) -> Certificate:
        """Create a new certificate.
        Args:
            :param certificate_authority: Certificate Authority to be used for signing
            :param names: Names field in the csr
            :param hosts: Hosts field in the csr
            :param common_name: Exact DNS match for which this certificate is valid
            :param label: a identifier to the certificate and key.
        """
        names = names or self.DEFAULT_NAMES
        key = self.key_provider.generate_key(common_name, names, hosts)
        certificate = self.sign_provider.sign(key, certificate_authority=certificate_authority)
        self.store[label] = certificate
        return certificate

    def get_or_create(self, label: str, *args, **kwargs) -> Certificate:
        """Creates new certificate, if it doesn't already exists"""
        if label in self.store:
            return self.store[label]
        return self.create(label, *args, **kwargs)

    def get(self, label: str) -> Certificate:
        """Returns already existing certificate from the store"""
        return self.store[label]

    def create_ca(
        self,
        label: str,
        hosts: List[str],
        names: Optional[List[Dict[str, str]]] = None,
        certificate_authority: Optional[Certificate] = None,
    ) -> Tuple[Certificate, UnsignedKey]:
        """Create a new certificate authority, if ca is specified it will create an intermediate ca.
        Args:
            :param certificate_authority:
            :param names: dict of all names
            :param hosts: list of hosts
            :param label: a identifier to the certificate and key.
        """
        names = names or self.DEFAULT_NAMES
        certificate, key = self.key_provider.generate_ca(label, names, hosts)
        if certificate_authority:
            certificate = self.sign_provider.sign_intermediate_ca(key, certificate_authority)
        self.store[label] = certificate
        return certificate, key

    def get_or_create_ca(self, label: str, *args, **kwargs) -> Certificate:
        """Creates new certificate authority, if one doesn't already exists"""
        if label in self.store:
            return self.store[label]
        certificate, _ = self.create_ca(label, *args, **kwargs)
        return certificate
