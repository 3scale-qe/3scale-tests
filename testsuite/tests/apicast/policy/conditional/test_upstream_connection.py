"testing proper function of upstream test connection with conditional policy"

import pytest
from packaging.version import Version

from testsuite import TESTED_VERSION, rawobj
from testsuite.utils import warn_and_skip

pytestmark = pytest.mark.skipif(TESTED_VERSION < Version("2.16"), reason="TESTED_VERSION < Version('2.16')")


# https://github.com/3scale/apicast-cloud-hosted
@pytest.fixture(scope="module", autouse=True)
def skip_saas(testconfig):
    """upstream_connection not available on SaaS"""
    if testconfig["threescale"]["deployment_type"] == "saas":
        warn_and_skip(skip_saas.__doc__)


@pytest.fixture(scope="module")
def backend_default(private_base_url, custom_backend):
    """
    Default backend with url from private_base_url.
    Have httpbin backend due to /delay implementation
    """
    return custom_backend("backend_default", endpoint=private_base_url("httpbin"))


@pytest.fixture(scope="module")
def policy_settings():
    "config of upstream connection policy with read_timeout set"
    return rawobj.PolicyConfig(
        "conditional",
        {
            "condition": {
                "operations": [
                    {"left": "{{ uri }}", "left_type": "liquid", "op": "==", "right": "/delay/2", "right_type": "plain"}
                ]
            },
            "policy_chain": [
                {
                    "name": "upstream_connection",
                    "configuration": {"connect_timeout": 1, "send_timeout": 1, "read_timeout": 1},
                }
            ],
        },
    )


def test_upstream_connection(api_client):
    "test read timeout behavior"
    client = api_client(disable_retry_status_list=[503, 500, 404])
    assert client.get("/delay/2").status_code == 504
    assert client.get("/delay/5").status_code == 200
