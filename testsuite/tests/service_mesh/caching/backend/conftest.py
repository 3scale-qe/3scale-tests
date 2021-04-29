"""Conftest for backend caching tests for service mesh"""

import pytest


@pytest.fixture(scope="module")
def gateway_environment():
    """Environment for backend caching tests"""
    return {"USE_CACHED_BACKEND": True, "BACKEND_CACHE_FLUSH_INTERVAL_SECONDS": 1000, "CACHE_ENTRIES_MAX": 1000}
