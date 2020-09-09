"""
Conftest for the jaeger tests
"""
import pytest

from testsuite.utils import blame
from testsuite.jaeger import Jaeger


@pytest.fixture(scope="module")
def jaeger(testconfig):
    """
    Returns the Jaeger client class used to communicate with jaeger
    configured based on the values from testconfig
    """
    return Jaeger(testconfig["fixtures"]["jaeger"]["url"],
                  testconfig["fixtures"]["jaeger"]["config"],
                  testconfig["ssl_verify"])


@pytest.fixture(scope="module")
def jaeger_randomized_name(request):
    """
    Randomized name for the jaeger configmap and for the jaeger service_name used
    when querying the services
    """
    return f"{blame(request, 'jaeger')}"


@pytest.fixture(scope="module")
def staging_gateway(staging_gateway, jaeger, jaeger_randomized_name):
    """
    Deploys template apicast gateway configured with jaeger.
    """
    staging_gateway.connect_jaeger(jaeger, jaeger_randomized_name)
    return staging_gateway
