"""Provide custom gateway for tests checking for Apicast Operator metrics."""

import pytest
from weakget import weakget

from testsuite.gateways import gateway
from testsuite.gateways.apicast.operator import OperatorApicast
from testsuite.utils import blame, warn_and_skip


@pytest.fixture(scope="module", autouse=True)
def require_openshift(testconfig):
    """These tests require openshift"""
    if not weakget(testconfig)["openshift"]["servers"]["default"] % False:
        warn_and_skip("All monitoring tests for apicast_operator skipped due to missing openshift")


@pytest.fixture(scope="module", autouse=True)
def require_prometheus_operator(prometheus):
    """These tests require configured operator for prometheus"""
    if not prometheus.operator_based:
        warn_and_skip("This test needs prometheus deployed by operator or OpenShift user workload monitoring")


@pytest.fixture(scope="module")
def staging_gateway(request):
    """Deploy self-managed operator based apicast gateway only to get namespace"""
    gw = gateway(kind=OperatorApicast, staging=True, name=blame(request, "gw"))
    request.addfinalizer(gw.destroy)
    gw.create()

    return gw
