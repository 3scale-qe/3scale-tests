"testing proper function of on_failed policy with conditional policy"

from packaging.version import Version  # noqa # pylint: disable=unused-import

import pytest

from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import

pytestmark = pytest.mark.skipif("TESTED_VERSION < Version('2.16')")


@pytest.fixture(scope="module")
def backend_default(private_base_url, custom_backend):
    """
    Default backend with url from private_base_url.
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
                    {"left": "{{ uri }}", "left_type": "liquid", "op": "==", "right": "/get", "right_type": "plain"}
                ]
            },
            "policy_chain": [
                {"name": "example", "version": "1.0", "configuration": {}},
                {"name": "on_failed", "version": "builtin", "configuration": {"error_status_code": 419}},
            ],
        },
    )


@pytest.mark.xfail
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-11738")
def test_on_failed(api_client):
    """if condition is met, non-existing policy is loaded and
    419 is returned by on_failed policy. Otherwise 200 is returned."""
    client = api_client(disable_retry_status_list=[503, 500, 404])
    assert client.get("/get").status_code == 419
    assert client.get("/").status_code == 200
