"""
Smoke performance test specific fixtures
"""
import pytest


@pytest.fixture(scope="module")
def number_of_agents():
    """Number of Hyperfoil agents to be spawned"""
    return 1
