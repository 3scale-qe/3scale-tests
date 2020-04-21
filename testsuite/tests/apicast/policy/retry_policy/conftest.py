"""Provide custom gateway for tests changing apicast parameters."""

import pytest

from testsuite.gateways import TemplateApicastOptions, TemplateApicast
from testsuite.utils import randomize


@pytest.fixture(scope="module")
def staging_gateway(configuration):
    """Deploy template apicast gateway."""
    settings_block = {
        "deployments": {
            "staging": randomize("retry-policy-staging"),
            "production": randomize("retry-policy-production")
        }
    }
    options = TemplateApicastOptions(staging=True, settings_block=settings_block, configuration=configuration)
    gateway = TemplateApicast(requirements=options)
    gateway.create()

    yield gateway

    gateway.destroy()
