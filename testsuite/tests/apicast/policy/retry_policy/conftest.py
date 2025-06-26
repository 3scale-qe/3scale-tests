"""Provide custom gateway for tests changing apicast parameters."""

import pytest
from weakget import weakget

from testsuite.gateways import gateway
from testsuite.gateways.apicast.template import TemplateApicast
from testsuite.utils import blame, warn_and_skip


@pytest.fixture(scope="module", autouse=True)
def require_openshift(testconfig):
    """These tests require openshift available"""
    if not weakget(testconfig)["openshift"]["servers"]["default"] % False:
        warn_and_skip("All retry_policy tests skipped due to missing openshift")


@pytest.fixture(scope="module")
def staging_gateway(request, testconfig):
    """Deploy self-managed template based apicast gateway."""
    gw = gateway(kind=TemplateApicast, staging=True, name=blame(request, "gw"))
    if not testconfig["skip_cleanup"]:
        request.addfinalizer(gw.destroy)
    gw.create()

    return gw
