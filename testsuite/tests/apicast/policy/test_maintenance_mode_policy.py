"""
A policy that allows you to reject incoming requests with a specified status code and message.
This policy should override others and reject all requests.
Expected: to return specified code eg 328 and message of service unavailability.
"""

import pytest
from testsuite import rawobj


@pytest.fixture(scope="module")
def policy_settings():
    """Have service with maintenance_mode policy added and configured to return custom message and code"""

    return rawobj.PolicyConfig("maintenance_mode", {
        "message_content_type": "text/plain; charset=utf-8",
        "status": 328,
        "message": "Service Unavailable - Maintenance"})


@pytest.mark.issue("https://issues.jboss.org/browse/THREESCALE-3189")
def test_maintenance_mode_policy(api_client):
    """Test request to service with maintenance_mode set returns appropriate message and status code"""

    response = api_client().get('/get')
    assert response.status_code == 328
    assert response.text == "Service Unavailable - Maintenance\n"
