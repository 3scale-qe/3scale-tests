"""Provide custom gateway for tests changing apicast parameters."""

import pytest

from testsuite.gateways import TemplateApicastOptions, TemplateApicast
from testsuite.capabilities import Capability
from testsuite.utils import randomize

pytestmark = pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY)


@pytest.fixture(scope="module")
def staging_gateway(configuration, request):
    """Deploy template apicast gateway."""
    settings_block = {
        "deployments": {
            "staging": randomize("retry-policy-staging"),
            "production": randomize("retry-policy-production")
        }
    }
    options = TemplateApicastOptions(staging=True, settings_block=settings_block, configuration=configuration)
    gateway = TemplateApicast(requirements=options)

    request.addfinalizer(gateway.destroy)
    gateway.create()

    return gateway
