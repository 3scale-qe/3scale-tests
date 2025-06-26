# pylint: disable=missing-module-docstring,wrong-import-position

import logging
import os
import socket
import sys
import time

if "_3SCALE_TESTS_DEBUG" in os.environ:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    # pylint: disable=invalid-name
    fmt = "%(asctime)s %(levelname)s:%(name)s:%(message)s"
    datefmt = "%H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt)
    # time in UTC
    formatter.converter = time.gmtime  # type: ignore
    handler.setFormatter(formatter)
    logger.addHandler(handler)

from pathlib import Path
from packaging.version import Version
from weakget import weakget
import importlib_resources as resources

from testsuite.config import settings  # noqa


# To avoid indefinite waiting on socket issues default timeout is used.
# Furthermore to avoid reset of timeout, monkey patching is used to alter
# socket.settimeout behavior
socket.setdefaulttimeout(120)
_socket_settimeout = socket.socket.settimeout


def _settimeout(self, timeout):
    """Monkey patch wrapper over original socket.settimeout

    This is to prevent disabling timeout on socket connection"""
    if timeout is None:
        timeout = socket.getdefaulttimeout()
    _socket_settimeout(self, timeout)


socket.socket.settimeout = _settimeout  # type: ignore


# Monkey patching! Yes! True power of dynamic language
# Let's modify 'BoxKeyError' to display a guidance as this is common error
# in case of missing openshift session (or dynaconf settings)
try:
    from box.exceptions import BoxKeyError  # pylint: disable=import-error
except ImportError:
    # pylint: disable=ungrouped-imports
    from dynaconf.vendor.box.exceptions import BoxKeyError

BoxKeyError.native_str = BoxKeyError.__str__
BoxKeyError.__str__ = (
    lambda self: self.native_str()
    + "\nHINT: Don't forget, either login to openshift (and set '3scale' project) or have all required config/ set!"
)

if settings["ssl_verify"]:
    for ca_bundle in (
        "/etc/pki/tls/certs/ca-bundle.crt",
        "/etc/ca-certificates/extracted/ca-bundle.trust.crt",
        "/etc/ssl/certs/ca-certificates.crt",
    ):
        if os.path.exists(ca_bundle):
            if "REQUESTS_CA_BUNDLE" not in os.environ:
                os.environ["REQUESTS_CA_BUNDLE"] = ca_bundle
            if "SSL_CERT_FILE" not in os.environ:
                os.environ["SSL_CERT_FILE"] = ca_bundle
            break
else:
    os.environ["OPENSHIFT_CLIENT_PYTHON_DEFAULT_SKIP_TLS_VERIFY"] = "true"

TESTED_VERSION = Version(
    str(
        weakget(settings)["threescale"]["version"]
        % resources.files("testsuite").joinpath("VERSION").read_text().strip()
    )
)
APICAST_OPERATOR_VERSION = Version(str(weakget(settings)["threescale"]["apicast_operator_version"] % 0))
HTTP2 = settings.get("http2", False)
ROOT_DIR = Path(os.path.abspath(__file__)).parent.parent
