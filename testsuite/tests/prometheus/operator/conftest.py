"""Verify we have prerequisites for Operator metrics tests."""

from weakget import weakget
import pytest

from testsuite.utils import warn_and_skip


@pytest.fixture(scope="module", autouse=True)
def require_openshift(testconfig):
    """These tests require openshift"""
    if not weakget(testconfig)["openshift"]["servers"]["default"] % False:
        warn_and_skip("All monitoring tests for 3scale-operator skipped due to missing openshift")


@pytest.fixture(scope="module", autouse=True)
def require_prometheus_operator(prometheus):
    """These tests require configured operator for prometheus"""
    if not prometheus.operator_based:
        warn_and_skip("This test needs prometheus deployed by operator or OpenShift user workload monitoring")
