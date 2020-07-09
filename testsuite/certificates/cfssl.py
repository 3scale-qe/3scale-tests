"""CFSSL certificate implementation."""
import contextlib
import json
import tempfile
import os
import subprocess
from typing import List, Dict

import cfssl

from testsuite.certificates import Certificate, CreateCertificateResponse


@contextlib.contextmanager
def cfssl_csr_jsonfile(request: cfssl.CertificateRequest):
    """Creates a temporary certificate request json file locally.

    Args:
        :param request: cfssl.CertificateRequest instance.

    Returns:
        File-like object containing certificate request json content.
    """
    content = json.dumps(request.to_api())

    jsonfile = tempfile.TemporaryFile(suffix='.json')
    try:
        jsonfile.write(content.encode('utf-8'))
        jsonfile.flush()
        jsonfile.seek(0, os.SEEK_SET)
        yield jsonfile
    finally:
        jsonfile.close()


class CFSSLCertificate(Certificate):  # pylint: disable=too-few-public-methods
    """CFSSL Certificate."""

    def __init__(self, host: str, port: int, ssl: bool = False,
                 verify_cert: bool = False):
        self.cfssl = cfssl.CFSSL(host, port, ssl=ssl, verify_cert=verify_cert)

    # pylint: disable=no-self-use
    def _get_csr(self, request: cfssl.CertificateRequest) -> Dict[str, str]:
        """Returns private key and CSR."""
        with cfssl_csr_jsonfile(request) as jsonfile:
            new_key = subprocess.Popen(['cfssl', 'genkey', '-'],
                                       stdin=jsonfile,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.DEVNULL)
            if not new_key.stdout:
                raise RuntimeError("Failed getting cfssl genkey output.")

            output = new_key.stdout.read()

            return json.loads(output)

    def create(self, common_name: str, names: List[str] = None,
               hosts: List[str] = None) -> CreateCertificateResponse:
        csr = self._get_csr(cfssl.CertificateRequest(common_name, names, hosts))
        cert = self.cfssl.sign(csr["csr"], hosts=hosts)
        return CreateCertificateResponse(certificate=cert, key=csr["key"])
