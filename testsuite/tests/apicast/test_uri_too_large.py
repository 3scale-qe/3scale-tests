"""Test for apicast logs with 414 Request-URI Too Large response"""
import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.capabilities import Capability

WARN_MESSAGES = [
    'using uninitialized "target_host" variable while logging request',
    'using uninitialized "post_action_impact" variable while logging request',
    'using uninitialized "access_logs_enabled" variable while logging request',
    'using uninitialized "extended_access_logs_enabled" variable while logging request',
]


pytestmark = [
    pytest.mark.required_capabilities(Capability.LOGS),
    pytest.mark.skipif("TESTED_VERSION < Version('2.13')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7906"),
    pytest.mark.issue("https://issues.redhat.com/browse/MGDAPI-5655"),
]


@pytest.fixture
def status_code(testconfig):
    """Expected status code based on testing environment"""
    if testconfig["threescale"]["deployment_type"] == "rhoam":
        return 503
    return 414


def test_uri_too_large(api_client, staging_gateway, status_code):
    """
    Test that redundant warn logs are not present in apicast logs after 414 Request-URI Too Large response
    """
    client = api_client()
    response = client.get(f"/{10000 * 'a'}")
    assert response.status_code == status_code
    logs = staging_gateway.get_logs()
    for message in WARN_MESSAGES:
        assert message not in logs


def test_param_too_large(api_client, staging_gateway, status_code):
    """
    Test that redundant warn logs are not present in apicast logs after 414 Request-URI Too Large response
    """
    client = api_client()
    response = client.get("/anything/anything", params={"long": 10000 * "a"})
    assert response.status_code == status_code
    logs = staging_gateway.get_logs()
    for message in WARN_MESSAGES:
        assert message not in logs
