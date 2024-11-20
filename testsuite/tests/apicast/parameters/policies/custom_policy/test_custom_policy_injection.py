"""Test for custom policy injected through operator with secret
"""

import pytest

from testsuite.capabilities import Capability


@pytest.mark.required_capabilities(Capability.OCP4)
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-9678")
@pytest.mark.nopersistence
# pylint: disable=unused-argument
def test_custom_policy(patch, application):
    """
    Sends request to apicast and check that the custom policy header is there
    """
    api_client = application.api_client()

    response = api_client.get("/")
    assert response.headers.get("X-Example-Policy-Response") == "TEST"
