"""Provide custom gateway for tests changing apicast parameters."""

from weakget import weakget
import pytest

from testsuite.gateways import gateway
from testsuite.gateways.apicast.operator import OperatorApicast
from testsuite.utils import blame, warn_and_skip


@pytest.fixture(scope="module", autouse=True)
def require_openshift(testconfig):
    """These tests require openshift available"""
    if not weakget(testconfig)["openshift"]["servers"]["default"] % False:
        warn_and_skip("All monitoring for selfmanaged apicast skipped due to missing openshift")


@pytest.fixture(scope="module", autouse=True)
def require_prometheus_operator(openshift):
    """require configured operator for prometheus"""
    routes = openshift().routes.for_service('prometheus-operated')
    if len(routes) == 0:
        warn_and_skip("This test needs prometheus deployed by operator")


@pytest.fixture(scope="module")
def staging_gateway(request):
    """Deploy self-managed template based apicast gateway."""
    gw = gateway(kind=OperatorApicast, staging=True, name=blame(request, "gw"))
    request.addfinalizer(gw.destroy)
    gw.create()

    return gw
