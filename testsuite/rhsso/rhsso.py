"""Module for backward compatibility of RHSSO imports, safe to delete if all references are changed"""

# pylint: disable=unused-import
from . import (  # noqa: F401
    OIDCClientAuth,
    OIDCClientAuthHook,
    RHSSOServiceConfiguration,
)
