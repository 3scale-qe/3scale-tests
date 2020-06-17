"""Conftest for backend caching tests for service mesh"""

import pytest


@pytest.fixture(scope="module")
def gateway_environment():
    """Environment for backend caching tests"""
    return {"THREESCALE_USE_CACHED_BACKEND": True}
