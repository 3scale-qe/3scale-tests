"""Provide custom gateway for tests changing apicast parameters."""
import pytest

from testsuite.gateways import TemplateApicastOptions, TemplateApicast
from testsuite.utils import blame


@pytest.fixture(scope="module")
def staging_gateway(request, configuration, settings_block, gateway_environment):
    """Deploy template apicast gateway."""
    options = TemplateApicastOptions(staging=True, settings_block=settings_block, configuration=configuration)
    gateway = TemplateApicast(requirements=options)
    gateway.create()

    if len(gateway_environment) > 0:
        gateway.environ.set_many(gateway_environment)

    request.addfinalizer(gateway.destroy)

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
