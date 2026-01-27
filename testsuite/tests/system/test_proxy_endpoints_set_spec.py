"""
Rewrite spec/functional_specs/proxy_endpoints_set_spec.rb
"""

import pytest

from testsuite.capabilities import Capability
from testsuite.utils import warn_and_skip

pytestmark = pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY)


def test_proxy_endpoints_set(service, testconfig):
    """
    Test checks if the endpoints match.
    """
    if testconfig["threescale"]["deployment_type"] == "saas":
        warn_and_skip("Different naming scheme for apicast on saas")

    service_name = service.entity["name"]
    tenant_name = "3scale"
    prefix = f"{service_name}-{tenant_name}"
    proxy = service.proxy.list()
    superdomain = testconfig["threescale"]["superdomain"]

    assert proxy["endpoint"] == f"https://{prefix}-apicast-production.{superdomain}:443"

    assert proxy["sandbox_endpoint"] == f"https://{prefix}-apicast-staging.{superdomain}:443"
