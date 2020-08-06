"""Rewrite of spec/openshift_specs/extract_access_log_spec.rb

Set `APICAST_ACCESS_LOG_FILE` parameter to apicast.
All access logs must be appended to the file set to the parameter.
"""
import re
from typing import Tuple
from urllib.parse import urlparse

import pytest

from testsuite.gateways.gateways import Capability

pytestmark = pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY)

ACCESS_LOG_FILE = "access.log"


@pytest.fixture(scope="module")
def gateway_environment(gateway_environment):
    """Sets location of the log file on the apicast"""
    gateway_environment.update({"APICAST_ACCESS_LOG_FILE": f"/tmp/{ACCESS_LOG_FILE}"})
    return gateway_environment


@pytest.fixture
def make_requests(api_client):
    """Make hits numbers of requests against gateway."""

    def run(hits):
        for _ in range(hits):
            assert api_client.get("/get").status_code == 200

    return run


@pytest.fixture
def read_log(staging_gateway, tmpdir):
    """Read log from gateway by copying it to a local directory.

    Returns a tuple containing the content of the file and also the
    number of lines logged into it.
    """

    def read(filename) -> Tuple[str, int]:
        source = f"/tmp/{filename}"

        dest = f"{tmpdir}/{filename}"

        # copy log file from apicast to local
        staging_gateway.openshift.rsync(staging_gateway.deployment, source, tmpdir)

        content = open(dest).read()
        # last empty item of the array is ignored
        lines = len(content.split("\n")) - 1

        return content, lines

    return read


@pytest.fixture
def api_backend_host(private_base_url):
    """Return only the hostname from private_base_url."""
    return urlparse(private_base_url()).hostname


def assert_backend_hosts_match(api_backend, content, hits):
    """Assert number of backend hosts hit matches hits."""
    assert len(re.findall(f"({api_backend})", content)) == hits


def test_access_log_lines_match_requests_hits(api_backend_host, make_requests, read_log):
    """Logs appended to access log file match number of requests made against gateway."""
    make_requests(3)

    content, lines = read_log(ACCESS_LOG_FILE)

    assert lines == 3

    assert_backend_hosts_match(api_backend_host, content, 3)
