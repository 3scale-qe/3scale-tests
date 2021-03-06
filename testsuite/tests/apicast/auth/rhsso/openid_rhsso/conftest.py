"""
Conftest for the openid rhsso credentials locations tests
"""

import pytest


@pytest.fixture(scope="module")
def staging_client(api_client):
    """
    Staging client
    The auth of the session is set up to none in order to test different auth methods
    The auth of the request will be passed in test functions
    """
    client = api_client()
    client.auth = None
    return client


@pytest.fixture(scope="module")
def production_client(prod_client):
    """
    Production client
    The auth of the session is set up to none in order to test different auth methods
    The auth of the request will be passed in test functions
    """
    client = prod_client()
    client.auth = None
    return client


@pytest.fixture
def token(application, rhsso_service_info):
    """Access token for 3scale application that is connected with RHSSO"""
    return rhsso_service_info.access_token(application)
