"""Test for large policy chain"""

import pytest
from packaging.version import Version

from testsuite import TESTED_VERSION, rawobj


@pytest.fixture()
def policy():
    """Creates a header policy that contains 10000 characters"""
    return rawobj.PolicyConfig("headers", {"response": [{"header": "Test-Header", "value": 10000 * "a"}]})


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-8377")
@pytest.mark.skipif(TESTED_VERSION < Version("2.14-dev"), reason="TESTED_VERSION < Version('2.14-dev')")
def test_long_policy_chain(policy, service):
    """
    Test creates a policy chain with size greater than 65,535 bytes 7 * header policy with 10000 characters
    """
    proxy = service.proxy.list()
    for _ in range(7):
        proxy.policies.append(policy)
