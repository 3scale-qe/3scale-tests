"""
Conftest for payload limits
"""

import backoff
import pytest


@pytest.fixture(scope="module")
def api_client(api_client):
    """
    Wrap api_client with a backoff retry on 404 to handle race conditions
    where APIcast staging hasn't loaded the new service configuration yet
    """

    def _api_client_with_retry(**kwargs):
        client = api_client(**kwargs)

        original_get = client.get

        @backoff.on_predicate(backoff.expo, lambda x: x.status_code == 404, max_tries=10, max_time=100)
        def get_with_retry(*args, **kwargs):
            return original_get(*args, **kwargs)

        client.get = get_with_retry

        return client

    return _api_client_with_retry
