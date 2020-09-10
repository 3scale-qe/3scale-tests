"""
Set of fixtures for Webhook-related tests.
"""
import pytest

from testsuite.requestbin import RequestBinClient


@pytest.fixture(scope="module")
def requestbin(testconfig):
    """
    Returns an instance of RequestBin.
    """
    return RequestBinClient(testconfig["requestbin"]["url"])
