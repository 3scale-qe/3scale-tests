"""Fixtures for tls related tests."""
import pytest

from testsuite.utils import blame

from testsuite.gateways import TLSApicast, TLSApicastOptions


@pytest.fixture(scope="module")
def staging_gateway(request, configuration):
    """Deploy tls apicast gateway."""
    settings_block = {
        "deployments": {
            "staging": blame(request, "tls-apicast"),
            "production": blame(request, "tls-apicast"),
        }
    }
    options = TLSApicastOptions(staging=True, settings_block=settings_block, configuration=configuration)
    gateway = TLSApicast(requirements=options)

    request.addfinalizer(gateway.destroy)
    gateway.create()

    return gateway
