"""logging policy tests shared fixtures"""

from weakget import weakget
import pytest

from testsuite.utils import warn_and_skip


@pytest.fixture(scope="module", autouse=True)
def require_openshift(testconfig):
    """These tests require openshift available"""
    if not weakget(testconfig)["openshift"]["servers"]["default"] % False:
        warn_and_skip("All from policy/logging skipped due to missing openshift")
