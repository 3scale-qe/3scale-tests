"""
Default conftest for rate limit tests
"""
import pytest
from pytest_cases import fixture_plus

from testsuite.utils import randomize


@pytest.fixture(scope="function")
def service_settings():
    """dict of service settings to be used when service created"""
    return {"name": randomize("service")}


@fixture_plus
def api_client(application, testconfig):
    """
    Sets ssl_verify for api client
    """
    return application.api_client(verify=testconfig["ssl_verify"])


@fixture_plus
def api_client2(application2, testconfig):
    """
    Sets ssl_verify for api client
    """
    return application2.api_client(verify=testconfig["ssl_verify"])
