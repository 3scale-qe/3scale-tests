"""Provide custom gateway for tests changing apicast parameters."""
from weakget import weakget
import pytest

from testsuite.gateways import gateway
from testsuite.gateways.apicast.template import TemplateApicast
from testsuite.utils import blame, warn_and_skip


@pytest.fixture(scope="module", autouse=True)
def require_openshift(testconfig):
    """These tests require openshift available"""
    if not weakget(testconfig)["openshift"]["servers"]["default"] % False:
        warn_and_skip("All from apicast/parameters skipped due to missing openshift")


@pytest.fixture(scope="module")
def staging_gateway(request, gateway_environment, gateway_options):
    """Deploy self-managed template based apicast gateway."""
    gw = gateway(kind=TemplateApicast, staging=True, name=blame(request, "gw"), **gateway_options)
    request.addfinalizer(gw.destroy)
    gw.create()

    if len(gateway_environment) > 0:
        gw.environ.set_many(gateway_environment)

    return gw


@pytest.fixture(scope="module")
def gateway_options():
    """Additional options to pass to staging gateway constructor"""
    return {}


@pytest.fixture(scope="module")
def gateway_environment():
    """Returns environment for Template apicast to use, the whole environment will be set in one command."""
    return {}
