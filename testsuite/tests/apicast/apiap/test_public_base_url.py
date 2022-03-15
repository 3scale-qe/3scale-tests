"""Test for Public Base URLs as localhost"""
import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import
from threescale_api.errors import ApiClientError

from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import

pytestmark = [
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7149"),
    pytest.mark.skipif("TESTED_VERSION < Version('2.12')")
]


def test_public_base_url(service):
    """
    Test:
        - try to update staging and production Public Base URLs to localhost
        - assert that it's not possible
    """
    thrown = False
    try:
        service.proxy.update(params={'endpoint': 'https://localhost:80'})
    except ApiClientError as error:
        thrown = True
        assert 'can\'t be localhost' in str(error)
    assert thrown, "Public Base URL for 3scale-managed gateway can't be set to localhost"
