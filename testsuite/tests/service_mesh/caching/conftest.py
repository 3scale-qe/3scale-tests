"""Conftest for all caching tests for service mesh"""
import pytest


@pytest.fixture(scope="module")
def staging_gateway(staging_gateway):
    """Sets environment for caching tests"""
    yield staging_gateway


@pytest.fixture(scope="module", autouse=True)
def setup_gateway(staging_gateway, gateway_environment):
    """Sets environment variables for gateway"""
    if len(gateway_environment) > 0:
        staging_gateway.environ().set_many(gateway_environment)


@pytest.fixture(scope="module")
def gateway_environment():
    """Allows setting environment for caching tests"""
    return {}
