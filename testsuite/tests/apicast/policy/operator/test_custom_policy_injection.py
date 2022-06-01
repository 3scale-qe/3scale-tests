"""Test for custom policy injected through secret
"""
import pytest

from testsuite.capabilities import Capability


# pylint: disable=unused-argument
@pytest.mark.disruptive
@pytest.mark.require_capabilities(Capability.OCP4)
def test_apimanager_custom_policy(patch_apimanager, application):
    """
    Sends request to apicast and check that the custom policy header is there
    """
    api_client = application.api_client()

    response = api_client.get("/")
    assert response.headers["X-Example-Policy-Response"] == "TEST"
