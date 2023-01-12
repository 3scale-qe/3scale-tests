"""Common conftest for all auth tests for ServiceMesh"""
import pytest

from testsuite.gateways.wasm import WASMGateway


@pytest.fixture(scope="session")
def no_auth_status_code(staging_gateway):
    """Auth code that the gateway will return when no auth is present,
    is different between Adapter and Extension"""
    if isinstance(staging_gateway, WASMGateway):
        return 403
    return 401
