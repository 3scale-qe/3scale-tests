# pylint: disable=missing-module-docstring,wrong-import-position

import os

from dynaconf import settings

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
CONFIGURATION: CommonConfiguration = CommonConfiguration()
