"""This is conftest. For master scoped tests."""

import pytest

from testsuite.utils import warn_and_skip


@pytest.fixture(scope="module", autouse=True)
def skip_saas(testconfig):
    """Custom tenant seem to be handled bit differently on SaaS"""
    if testconfig["threescale"]["deployment_type"] == "saas":
        warn_and_skip(skip_saas.__doc__)
