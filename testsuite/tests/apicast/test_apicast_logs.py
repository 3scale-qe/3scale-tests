"""Test for apicast logs shows permission denied in a tmp file"""

import re

import pytest


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7942")
def test_apicast_logs_tmp_file(staging_gateway):
    """
    Test that the logs don't contain permission denied in a tmp file
    """
    assert not re.search("env: '/tmp/[a-zA-Z0-9]*': Permission denied", staging_gateway.get_logs())


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7941")
def test_apicast_logs_nginx_warn(staging_gateway):
    """
    Test that the logs don't contain nginx warn
    """
    log = (
        "nginx: [warn] could not build optimal variables_hash, you should increase either variables_hash_max_size: "
        "1024 or variables_hash_bucket_size: 64; ignoring variables_hash_bucket_size"
    )
    assert log not in staging_gateway.get_logs()
