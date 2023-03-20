"""Conftest for all policies tests"""
import pytest


@pytest.fixture(scope="module")
def policy_settings():
    """This does nothing; enables to setup policies in test files"""
    return None


@pytest.fixture(scope="module")
def service(service, policy_settings):
    """Add policy to the first service"""
    service.proxy.list().policies.append(policy_settings)
    return service
