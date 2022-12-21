"""Common conftest for all auth tests for ServiceMesh"""
import pytest

from testsuite.gateways.wasm import WASMGateway, WASMExtension


@pytest.fixture(scope="session")
def no_auth_status_code(staging_gateway):
    """Auth code that the gateway will return when no auth is present,
    is different between Adapter and Extension"""
    if isinstance(staging_gateway, WASMGateway):
        return 403
    return 401


@pytest.fixture(scope="module")
def extension(staging_gateway, service) -> WASMExtension:
    """Returns extension associated with default service"""
    return staging_gateway.get_extension(service)
