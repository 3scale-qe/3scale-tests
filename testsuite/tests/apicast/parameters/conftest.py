"""Provide custom gateway for tests changing apicast parameters."""
import pytest

from testsuite.gateways import TemplateApicastOptions, TemplateApicast


@pytest.yield_fixture(scope="module")
def staging_gateway(configuration):
    """Deploy template apicast gateway."""
    settings_block = {
        "deployments": {
            "staging": "openshift-tests-staging",
            "production": "openshift-tests-production"
        }
    }
    options = TemplateApicastOptions(staging=True, settings_block=settings_block, configuration=configuration)
    gateway = TemplateApicast(requirements=options)
    gateway.create()

    yield gateway

    gateway.destroy()
