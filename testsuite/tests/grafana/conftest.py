"""Check for openshift configuration"""

from openshift import Missing
from weakget import weakget
import pytest

from testsuite.utils import warn_and_skip


@pytest.fixture(scope="module", autouse=True)
def require_openshift(testconfig):
    """These tests require openshift available"""
    if not weakget(testconfig)["openshift"]["servers"]["default"] % False:
        warn_and_skip("All monitoring for Grafana skipped due to missing openshift")


@pytest.fixture(scope="module", autouse=True)
def require_enabled_monitoring(openshift):
    """Verify that monitoring is enabled in APIManager object"""
    apimanager = openshift().api_manager

    if apimanager.model.spec.monitoring is Missing or not apimanager.model.spec.monitoring.enabled:
        warn_and_skip("Monitoring needs to be enabled in APIManager Object")
