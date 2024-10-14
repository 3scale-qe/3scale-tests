"""Module that helps certificates with temporary persistence"""

import os
import shutil
import tempfile
from abc import ABC, abstractmethod
from typing import Dict


class TmpFilePersist(ABC):
    """Persists data into files so it can be used in commands that require files"""

    def __init__(self) -> None:
        super().__init__()
        self._files = None
        self._dir = None

    @property
    def _directory(self):
        if not self._dir:
            self._dir = tempfile.mkdtemp(prefix="tls_certs_", dir=os.environ.get("resultsdir"))
        return self._dir

    @abstractmethod
    def persist(self):
        """Saves current class to a tmp file"""

    def _persist(self, **kwargs) -> Dict[str, str]:
        files = {}
        for key, value in kwargs.items():
            path = os.path.join(self._directory, key)
            with open(path, "w", encoding="utf8") as file:
                file.write(value)
            files[key] = path
        return files

    @property
    def files(self):
        """Returns tuple of information about files this class has"""
        if not self._files:
            self._files = self.persist()
        return self._files

    def delete_files(self):
        """Deletes temporary files"""
        if self._files:
            shutil.rmtree(self._dir)
            self._files = None
            self._dir = None
