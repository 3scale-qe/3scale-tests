"""
Conftest for the openid rhsso credentials locations tests
"""

import backoff
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

    original_get = client.get
    original_post = client.post

    @backoff.on_predicate(backoff.expo, lambda x: x.status_code == 404, max_tries=10, max_time=60)
    def get_with_retry(*args, **kwargs):
        return original_get(*args, **kwargs)

    @backoff.on_predicate(backoff.expo, lambda x: x.status_code == 404, max_tries=10, max_time=60)
    def post_with_retry(*args, **kwargs):
        return original_post(*args, **kwargs)

    client.get = get_with_retry
    client.post = post_with_retry

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
