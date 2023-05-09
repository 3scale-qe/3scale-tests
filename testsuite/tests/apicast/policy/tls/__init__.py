"""Module containing TLS tests"""
import base64


def embedded(pem: str, name: str, app: str) -> str:
    """Returns data formatted for embedded configuration."""
    b64 = base64.b64encode(pem.encode("ascii")).decode("ascii")
    data = [f"data:application/{app}", f"name={name}", f"base64,{b64}"]
    return ";".join(data)
