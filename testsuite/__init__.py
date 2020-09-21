# pylint: disable=missing-module-docstring,wrong-import-position

import logging
import os

if "_3SCALE_TESTS_DEBUG" in os.environ:
    logging.basicConfig(level=logging.DEBUG)

from pathlib import Path

from dynaconf import settings

# Monkey patching! Yes! True power of dynamic language
# Let's modify 'BoxKeyError' to display a guidance as this is common error
# in case of missing openshift session (or dynaconf settings)
try:
    from box.exceptions import BoxKeyError  # pylint: disable=import-error
except ImportError:
    # pylint: disable=ungrouped-imports
    from dynaconf.vendor.box.exceptions import BoxKeyError

BoxKeyError.native_str = BoxKeyError.__str__
BoxKeyError.__str__ = lambda self: \
    self.native_str() + \
    "\nHINT: Don't forget, either login to openshift (and set '3scale' project) or have all required config/ set!"

if settings["ssl_verify"]:
    if "REQUESTS_CA_BUNDLE" not in os.environ:
        for ca_bundle in (
                "/etc/pki/tls/certs/ca-bundle.crt",
                "/etc/ca-certificates/extracted/ca-bundle.trust.crt",
                "/etc/ssl/certs/ca-certificates.crt"):
            if os.path.exists(ca_bundle):
                os.environ["REQUESTS_CA_BUNDLE"] = ca_bundle
                break
else:
    os.environ["OPENSHIFT_CLIENT_PYTHON_DEFAULT_SKIP_TLS_VERIFY"] = "true"

from packaging.version import Version  # noqa: E402
from testsuite.configuration import CommonConfiguration  # noqa: E402

TESTED_VERSION = Version(str(settings["threescale"]["version"]))
HTTP2 = settings.get("http2", False)
ROOT_DIR = Path(os.path.abspath(__file__)).parent.parent
CONFIGURATION: CommonConfiguration = CommonConfiguration()
