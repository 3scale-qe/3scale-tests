"Provides custom service to add policy to policy chain"

import pytest


@pytest.fixture(scope="module")
def policy_settings():
    "This does nothing; enables to skip policy_settings in test files"
    return None


@pytest.fixture(scope="module")
def service(service, policy_settings):
    """Service with prepared policy_settings added"""
    if policy_settings is not None:
        if not isinstance(policy_settings, list):
            policy_settings = [policy_settings]
        service.proxy.list().policies.append(*policy_settings)

    return service
