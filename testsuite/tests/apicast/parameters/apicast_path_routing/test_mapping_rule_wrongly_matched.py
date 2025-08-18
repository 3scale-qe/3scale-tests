"""
Test that URL with space in a parameter will be sent to the correct service when the
APICAST_PATH_ROUTING is in use
"""

import pytest
from packaging.version import Version

from testsuite import TESTED_VERSION
from testsuite.capabilities import Capability

pytestmark = [
    pytest.mark.skipif(TESTED_VERSION < Version("2.9"), reason="TESTED_VERSION < Version('2.9')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-4152"),
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT),
]


@pytest.fixture(scope="module")
def gateway_environment(gateway_environment):
    """Enables path routing on gateway"""
    gateway_environment.update({"APICAST_PATH_ROUTING": True})
    return gateway_environment


@pytest.fixture(scope="module")
def service_mapping():
    """Change mapping rule for service"""
    return "/foo/{anything}/bar"


@pytest.fixture(scope="module")
def service2_mapping():
    """Change mapping rule for service2"""
    return "/ip/{anything}"


# pylint: disable=unused-argument
def test_mapping_rule_wrongly_matched(application2, client):
    """
    service2 has to be created before service

    Makes a request to an endpoint containing a space char.
    Asserts that the response is not "no mapping rule matched"
    """
    response = client.get("/foo/123 123/bar")
    assert response.status_code == 200
