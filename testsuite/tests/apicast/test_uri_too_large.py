"""Test for apicast logs with 414 Request-URI Too Large response"""
import pytest

WARN_MESSAGES = [
    'using uninitialized "target_host" variable while logging request',
    'using uninitialized "post_action_impact" variable while logging request',
    'using uninitialized "access_logs_enabled" variable while logging request',
    'using uninitialized "extended_access_logs_enabled" variable while logging request',
]


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7906")
def test_uri_too_large(api_client, staging_gateway):
    """
    Test that redundant warn logs are not present in apicast logs after 414 Request-URI Too Large response
    """
    client = api_client()
    response = client.get(f"/{10000 * 'a'}")
    assert response.status_code == 414
    logs = staging_gateway.get_logs()
    for message in WARN_MESSAGES:
        assert message not in logs
