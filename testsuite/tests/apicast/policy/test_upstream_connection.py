"testing proper function of upstream test connection"

from packaging.version import Version  # noqa # pylint: disable=unused-import

import pytest

from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import

pytestmark = pytest.mark.skipif("TESTED_VERSION < Version('2.6')")


@pytest.fixture(scope="module")
def policy_settings():
    "config of upstream connection policy with read_timeout set"
    return rawobj.PolicyConfig("upstream_connection", {"read_timeout": 5})


def test_upstream_connection(testconfig, application):
    "test read timeout behavior"
    verify = testconfig["ssl_verify"]
    assert application.test_request("/delay/3", verify=verify).status_code == 200
    assert application.test_request("/delay/9", verify=verify).status_code == 504
