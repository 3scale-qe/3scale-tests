"""Test for custom policy injected through secret
"""
import pytest


# pylint: disable=unused-argument
@pytest.mark.disruptive
def test_apimanager_custom_policy(patch_apimanager, application):
    """
    Sends request to apicast and check that the custom policy header is there
    """
    api_client = application.api_client()

    response = api_client.get("/")
    assert response.headers["X-Example-Policy-Response"] == "TEST"
