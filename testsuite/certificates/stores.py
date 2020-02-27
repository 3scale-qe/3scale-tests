"""CertificateStore concrete classes."""
import os
import tempfile

from testsuite.certificates import CertificateStore, GetCertificateResponse


class TmpCertificateStore(CertificateStore):
    """Enable temporary certificate persistency in local disk."""

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
