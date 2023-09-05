"""Test for apicast logs shows permission denied in a tmp file"""

import re

import pytest


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7942")
def test_apicast_logs(staging_gateway):
    """
    Test that the logs don't contain permission denied in a tmp file
    """
    assert not re.search("env: '/tmp/[a-zA-Z0-9]*': Permission denied", staging_gateway.get_logs())
