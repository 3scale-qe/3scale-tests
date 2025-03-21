"""conftest for conditional tests"""

import pytest

from testsuite.mockserver import Mockserver


@pytest.fixture(scope="module")
def base_url_mockserver(private_base_url):
    """Backend API URL"""
    return private_base_url("mockserver+ssl")


@pytest.fixture(scope="module")
def mockserver(base_url_mockserver, testconfig):
    """Have mockerver to setup failing requests for certain occurrences"""
    return Mockserver(base_url_mockserver, testconfig["ssl_verify"])
