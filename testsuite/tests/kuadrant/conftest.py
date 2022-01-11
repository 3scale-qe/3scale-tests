""" Conftest file for Kuadrant. """

import pytest
import utils


@pytest.fixture(scope="module")
def api_client(request):
    """
    Fixture that returns api_client
    Returns:
        api_client (HttpClient): Api client for application
    """
    def _api_client(**kwargs):
        client = utils.HttpClient(**kwargs)
        request.addfinalizer(client.close)
        return client

    return _api_client
