"""Provide custom gateway for tests changing apicast parameters."""
from weakget import weakget
import pytest

from testsuite.gateways import TemplateApicastOptions, TemplateApicast
from testsuite.utils import blame, warn_and_skip


@pytest.fixture(scope="module", autouse=True)
def require_openshift(testconfig):
    """These tests require openshift available"""
    if not weakget(testconfig)["openshift"]["servers"]["default"] % False:
        warn_and_skip("All from apicast/parameters skipped due to missing openshift")


@pytest.fixture(scope="module")
def staging_gateway(request, configuration, settings_block, gateway_environment):
    """Deploy template apicast gateway."""

    options = TemplateApicastOptions(staging=True, settings_block=settings_block, configuration=configuration)
    gateway = TemplateApicast(requirements=options)

    request.addfinalizer(gateway.destroy)

    gateway.create()

    if len(gateway_environment) > 0:
        gateway.environ.set_many(gateway_environment)

    return gateway


@pytest.fixture(scope="module")
def settings_block(request):
    """Settings block for staging gateway"""
    return {
        "deployments": {
            "staging": blame(request, "staging"),
            "production": blame(request, "production")
        }
    }


@pytest.fixture(scope="module")
def gateway_environment():
    """Returns environment for Template apicast to use, the whole environment will be set in one command."""
    return {}
