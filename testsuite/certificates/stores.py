"""CertificateStore concrete classes."""

import os
import tempfile
from abc import ABC
from typing import Dict

from testsuite.certificates import Certificate, CertificateStore


def _persist(path, name: str, ext: str, content: str):
    with open(os.path.join(path, f"{name}.{ext}"), "w", encoding="utf8") as file:
        file.write(content)


def _read(path, name: str, ext: str) -> str:
    with open(os.path.join(path, f"{name}.{ext}"), "r", encoding="utf8") as file:
        content = file.read()
    return content


class TmpCertificateStore(CertificateStore, ABC):
    """
    Enable temporary certificate persistency in local disk.
    Obsolete as tmp files have no advantage over InMemoryStore
    """

    def __init__(self):
        self.path = tempfile.mkdtemp("certs")

    def _get_label_path(self, label: str):
        return os.path.join(self.path, label)

    def __contains__(self, key: str):
        return os.path.exists(self._get_label_path(key))

    def __setitem__(self, key: str, value: Certificate):
        path = self._get_label_path(key)
        if not os.path.exists(path):
            os.makedirs(path)
        _persist(path, "certificate", "crt", value.certificate)
        _persist(path, "key", "key", value.key)

    def __getitem__(self, key: str):
        path = self._get_label_path(key)
        cert = _read(path, "certificate", "crt")
        key = _read(path, "key", "key")
        return Certificate(certificate=cert, key=key)


class InMemoryCertificateStore(CertificateStore):
    """Certificates which stores data in memory, or to be more precise, in a dict"""

    def __init__(self) -> None:
        self.data: Dict[str, Certificate] = {}

    def __contains__(self, key: str):
        return key in self.data

    def __setitem__(self, key: str, value: Certificate):
        self.data[key] = value

    def __getitem__(self, key: str):
        return self.data[key]
