"""
Conftest for the jaeger tests
"""

import pytest
from weakget import weakget

from testsuite.jaeger import Jaeger


@pytest.fixture(scope="module")
def jaeger(testconfig, tools):
    """
    Returns the Jaeger client class used to communicate with jaeger
    configured based on the values from testconfig
    """

    url = weakget(testconfig)["fixtures"]["jaeger"]["url"] % tools["jaeger"]
    return Jaeger(url, testconfig["fixtures"]["jaeger"]["config"], testconfig["ssl_verify"])


@pytest.fixture(scope="module")
def jaeger_service_name(staging_gateway, jaeger):
    """
    Deploys apicast gateway configured with jaeger.
    """
    name = staging_gateway.connect_open_telemetry(jaeger)
    yield name
    staging_gateway.disconnect_open_telemetry(name)
