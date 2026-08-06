"""
Test that user defined environment variables persist through APIcast operator reconciliation.

This test validates the fix for THREESCALE-12224.
"""

import pytest
from packaging.version import Version

from testsuite import TESTED_VERSION
from testsuite.capabilities import Capability

pytestmark = [
    pytest.mark.sandbag,  # Test uses operator, is slow
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-12224"),
    pytest.mark.required_capabilities(Capability.OCP4),
    pytest.mark.skipif(TESTED_VERSION < Version("2.16.4"), reason="TESTED_VERSION < Version('2.16.4')"),
]


@pytest.fixture(scope="module")
def gw_with_user_env(staging_gateway, logger):
    """
    Adds environment variables to the APIcast deployment.
    """

    test_env_var_name = "APICAST_PATH_ROUTING_ONLY"
    test_env_var_value = "true"

    environ = staging_gateway.deployment.environ()
    environ.refresh()

    logger.info("Adding env var: %s=%s", test_env_var_name, test_env_var_value)
    environ[test_env_var_name] = test_env_var_value

    environ.refresh()
    assert environ[test_env_var_name] == test_env_var_value, "Env var was not set correctly"

    return environ, test_env_var_name, test_env_var_value


def test_user_env_var_persists(gw_with_user_env, staging_gateway):
    """Verify user defined vars remain after reconciliation"""
    environ, test_env_var_name, test_env_var_value = gw_with_user_env

    # Trigger reconciliation by modifying a supported env var that goes through the operator
    staging_gateway.environ["APICAST_LOG_LEVEL"] = "debug"
    staging_gateway.deployment.wait_for()

    environ.refresh()

    try:
        current_value = environ[test_env_var_name]
        assert (
            current_value == test_env_var_value
        ), f"Env var changed after reconciliation. Expected: {test_env_var_value}, got {current_value}"
    except KeyError:
        pytest.fail(f"FAILURE: User-defined env var '{test_env_var_name}' was removed during operator reconciliation.")
