"""Module containing classes for local CFSSL"""
import json
import os
import subprocess
from typing import Optional, List, Tuple, Dict, Any

import importlib_resources as resources

from testsuite.certificates import KeyProvider, SigningProvider, Certificate, UnsignedKey
from testsuite.certificates.cfssl import CFSSLException


class CFSSLProviderCLI(KeyProvider, SigningProvider):
    """Generates certificates and signs them using local CFSSL binary"""

    def __init__(self, binary) -> None:
        super().__init__()
        self.binary = binary

    def _execute_command(self,
                         command: str,
                         *args: str,
                         stdin: Optional[str] = None):
        args = (self.binary, command, *args)
        try:
            response = subprocess.run(args,
                                      stderr=subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      input=stdin,
                                      universal_newlines=bool(stdin),
                                      check=False)
            if response.returncode != 0:
                raise CFSSLException(f"CFSSL command {args} returned non-zero response code, error {response.stderr}")
            return json.loads(response.stdout)
        except Exception as exception:
            # If some error occurs, first check if the binary exists to throw better error
            if not os.path.exists(self.binary):
                raise AttributeError("CFSSL binary does not exist") from exception
            raise exception

    def generate_key(self, common_name: str, names: Optional[List[Dict[str, str]]] = None,
                     hosts: Optional[List[str]] = None) -> UnsignedKey:
        data: Dict[str, Any] = {
            "CN": common_name
        }
        if names:
            data["names"] = names
        if hosts:
            data["hosts"] = hosts

        result = self._execute_command("genkey", "-", stdin=json.dumps(data))
        return UnsignedKey(key=result["key"], csr=result["csr"])

    def sign_intermediate_ca(self, key: UnsignedKey, certificate_authority: Certificate) -> Certificate:
        args = [
            f"-ca={certificate_authority.files['certificate']}",
            f"-ca-key={certificate_authority.files['key']}",
            f"-config={resources.files('testsuite.resources.tls').joinpath('intermediate_config.json')}"
        ]
        result = self._execute_command("sign", *args, "-", stdin=key.csr)
        return Certificate(key=key.key, certificate=result["cert"])

    def sign(self, key: UnsignedKey, certificate_authority: Optional[Certificate] = None) -> Certificate:
        args = []
        if certificate_authority:
            args.append(f"-ca={certificate_authority.files['certificate']}")
            args.append(f"-ca-key={certificate_authority.files['key']}")
        result = self._execute_command("sign", *args, "-", stdin=key.csr)
        return Certificate(key=key.key, certificate=result["cert"])

    def generate_ca(self, common_name: str,
                    names: List[Dict[str, str]],
                    hosts: List[str]) -> Tuple[Certificate, UnsignedKey]:
        data = {
            "CN": common_name,
            "names": names,
            "hosts": hosts
        }

        result = self._execute_command("genkey", "-initca", "-", stdin=json.dumps(data))
        key = UnsignedKey(key=result["key"], csr=result["csr"])
        cert = Certificate(key=result["key"], certificate=result["cert"])
        return cert, key
