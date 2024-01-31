"""
Tests strict backend caching (unknown credentials are forbidden) in the adapter
"""

import pytest

from testsuite.capabilities import Capability


@pytest.fixture(scope="module")
def gateway_environment(gateway_environment):
    """Ensure that the strict caching is enabled even if it is not the default in the future"""
    gateway_environment["BACKEND_CACHE_POLICY_FAIL_CLOSED"] = "True"
    return gateway_environment


@pytest.mark.required_capabilities(Capability.SERVICE_MESH_ADAPTER)
@pytest.mark.disruptive
def test_caching_policy_strict(api_client, openshift):
    """
    Test caching policy with caching mode set to Strict

    To cache credentials:
        - make request to production gateway with valid credentials
        - make request to production gateway with invalid credentials
    Scale backend-listener down
    Test if:
        - response with valid credentials have status_code == 200
        - response with same invalid credentials should still fail because invalid credentials are not cached
    Scale backend-listener up to old value
    Now the requests should act as usual.
    """

    client = api_client()
    response = client.get("/", params=None)
    assert response.status_code == 200

    with openshift().scaler.scale("backend-listener", 0):
        # Test if response succeed on production calls with valid credentials
        for _ in range(3):
            response = client.get("/", params=None)
            assert response.status_code == 200

        # Test if response fails on production calls with invalid credentials
        for _ in range(3):
            response = client.get("/", params={"user_key": ":user_key"})
            assert response.status_code != 200

    # Test that adapter works after backend is back online
    response = client.get("/", params={"user_key": ":user_key"})
    assert response.status_code == 403

    response = client.get("/", params=None)
    assert response.status_code == 200
