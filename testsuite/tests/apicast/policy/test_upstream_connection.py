"testing proper function of upstream test connection"

from packaging.version import Version  # noqa # pylint: disable=unused-import

import pytest

from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.utils import warn_and_skip

pytestmark = pytest.mark.skipif("TESTED_VERSION < Version('2.6')")


@pytest.fixture(scope="module", autouse=True)
def skip_saas(testconfig):
    """upstream_connection not available on SaaS"""
    if testconfig["threescale"]["deployment_type"] == "saas":
        warn_and_skip(skip_saas.__doc__)


@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url):
    """Have httpbin backend due to /delay implementation"""

    return rawobj.Proxy(private_base_url("httpbin"))


@pytest.fixture(scope="module")
def policy_settings():
    "config of upstream connection policy with read_timeout set"
    return rawobj.PolicyConfig("upstream_connection", {"read_timeout": 5})


def test_upstream_connection(api_client):
    "test read timeout behavior"
    client = api_client()
    assert client.get("/delay/3").status_code == 200
    assert client.get("/delay/9").status_code == 504
