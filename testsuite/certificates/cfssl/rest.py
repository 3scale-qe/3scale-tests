"""CFSSL certificate implementation."""
from typing import Optional

import cfssl

from testsuite.certificates import Certificate, SigningProvider, UnsignedKey


class CFSSLRESTProvider(SigningProvider):  # pylint: disable=too-few-public-methods
    """Class for signing keys with remote CFSSL instance."""

    def sign(self, key: UnsignedKey, certificate_authority: Optional[Certificate] = None) -> Certificate:
        certificate = self.cfssl.sign(key.csr, hosts=[])
        return Certificate(key=key.key, certificate=certificate)

    def __init__(self, host: str, port: int, ssl: bool = False,
                 verify_cert: bool = False):
        self.cfssl = cfssl.CFSSL(host, port, ssl=ssl, verify_cert=verify_cert)
