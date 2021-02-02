"""
Set of fixtures for Webhook-related tests.
"""
from weakget import weakget

import pytest

from testsuite.requestbin import RequestBinClient


@pytest.fixture(scope="module")
def requestbin(testconfig, tools):
    """
    Returns an instance of RequestBin.
    """

    return RequestBinClient(weakget(testconfig)["requestbin"]["url"] % tools["request-bin"])
