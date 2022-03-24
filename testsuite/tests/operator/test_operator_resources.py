"""
Test 3scale Operator pod resource limits and requests
"""

import re
import pytest

from packaging.version import Version
from testsuite import TESTED_VERSION
from testsuite.capabilities import Capability

pytestmark = [pytest.mark.skipif("TESTED_VERSION < Version('2.10')"),
              pytest.mark.required_capabilities(Capability.OCP4)]


def test_operator_resources(openshift):
    """
    Test if operator pod has proper resources defined
    """
    operator_pod = openshift().get_operator()
    describe_output = operator_pod.describe()

    if TESTED_VERSION < Version('2.11'):
        # 2.10-GA
        assert not re.search(r'Limits:', describe_output)
        assert re.search(r'Requests:\s+cpu:\s+10m\s+memory:\s+100m', describe_output)
    elif TESTED_VERSION < Version('2.12'):
        # 2.11-alpha
        assert re.search(r'Limits:\s+cpu:\s+100m\s+memory:\s+100Mi', describe_output)
        assert re.search(r'Requests:\s+cpu:\s+100m\s+memory:\s+100Mi', describe_output)
    else:
        assert re.search(r'Limits:\s+cpu:\s+100m\s+memory:\s+300Mi', describe_output)
        assert re.search(r'Requests:\s+cpu:\s+100m\s+memory:\s+300Mi', describe_output)
