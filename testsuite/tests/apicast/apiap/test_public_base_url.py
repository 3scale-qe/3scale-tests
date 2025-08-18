"""Test for Public Base URLs as localhost"""

import pytest
from packaging.version import Version
from threescale_api.errors import ApiClientError

from testsuite import TESTED_VERSION

pytestmark = [
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7149"),
    pytest.mark.skipif(TESTED_VERSION < Version("2.12"), reason="TESTED_VERSION < Version('2.12')"),
]


def test_public_base_url(service):
    """
    Test:
        - try to update staging and production Public Base URLs to localhost
        - assert that it's not possible
    """
    with pytest.raises(ApiClientError) as exc_info:
        service.proxy.update(params={"endpoint": "https://localhost:80"})
    assert r"can\'t be localhost" in str(exc_info.value)
