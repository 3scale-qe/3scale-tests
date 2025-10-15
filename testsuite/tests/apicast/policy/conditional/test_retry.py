"testing proper function of retry policy with conditional policy"

from packaging.version import Version  # noqa # pylint: disable=unused-import

import pytest

from testsuite.capabilities import Capability
from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.utils import blame, generate_tail
from testsuite.gateways import gateway
from testsuite.gateways.apicast.template import TemplateApicast


pytestmark = pytest.mark.skipif("TESTED_VERSION < Version('2.16')")
pytestmark = pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT)


@pytest.fixture(scope="module")
def backend_default(private_base_url, custom_backend):
    """
    Default backend with url from private_base_url.
    Have httpbin backend due to /delay implementation
    """
    return custom_backend("backend_default", endpoint=private_base_url("mockserver+ssl"))


@pytest.fixture(scope="module")
def staging_gateway(request, testconfig):
    """Sets apicast env variable"""
    gw = gateway(kind=TemplateApicast, staging=True, name=blame(request, "gw"))
    if not testconfig["skip_cleanup"]:
        request.addfinalizer(gw.destroy)
    gw.create()

    gw.environ["APICAST_UPSTREAM_RETRY_CASES"] = "http_500"
    return gw


@pytest.fixture(scope="module")
def fail_request_suffix():
    """Generate unique suffix for fail requests to avoid interference with other tests"""
    return f"-{generate_tail()}"


@pytest.fixture(scope="module")
def policy_settings(fail_request_suffix):
    "config of upstream connection policy with read_timeout set"
    return rawobj.PolicyConfig(
        "conditional",
        {
            "condition": {
                "operations": [
                    {
                        "left": "{{ uri }}",
                        "left_type": "liquid",
                        "op": "==",
                        "right": f"/fail-request{fail_request_suffix}/5/500",
                        "right_type": "plain",
                    }
                ]
            },
            "policy_chain": [{"name": "retry", "configuration": {"retries": 5}}],
        },
    )


def test_retry(api_client, mockserver, fail_request_suffix):
    "test read timeout behavior"
    client = api_client(disable_retry_status_list=[503, 500, 404])

    mockserver.temporary_fail_request(5, suffix=fail_request_suffix)
    assert client.get(f"/fail-request{fail_request_suffix}/5/500").status_code == 200
    mockserver.temporary_fail_request(1, suffix=fail_request_suffix)
    assert client.get(f"/fail-request{fail_request_suffix}/1/500").status_code == 500
