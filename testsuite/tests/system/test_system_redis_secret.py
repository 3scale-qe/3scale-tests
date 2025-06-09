"""Tests for MessageBus variables in system-redis secret"""

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import

pytestmark = [
    pytest.mark.sandbag,  # requires openshift
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7822"),
]

KEYS = [
    "MESSAGE_BUS_NAMESPACE",
    "MESSAGE_BUS_SENTINEL_HOSTS",
    "MESSAGE_BUS_SENTINEL_ROLE",
    "MESSAGE_BUS_URL",
]


@pytest.fixture(scope="session")
def system_redis_secret(openshift):
    """return system-redis secret"""
    secret = openshift().secrets["system-redis"]
    return secret


@pytest.mark.skipif("TESTED_VERSION >= Version('2.12')")
@pytest.mark.parametrize("key", KEYS)
def test_message_bus_secrets(system_redis_secret, key):
    """test of env variable presence"""
    assert key in system_redis_secret


@pytest.mark.skipif("TESTED_VERSION < Version('2.12')")
@pytest.mark.parametrize("key", KEYS)
def test_message_bus_secrets_missing(system_redis_secret, key):
    """test of env variable absence"""
    assert key not in system_redis_secret
