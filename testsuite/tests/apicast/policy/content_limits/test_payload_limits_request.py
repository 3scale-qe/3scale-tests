"""
Testing that the request/response content limit policy limits the content-length of the
request body
"""
import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite.utils import random_string
from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import

pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.10')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5244"),
]


@pytest.fixture(scope="module")
def policy_settings():
    """
    Enable the content limits policy and sets the request limit
    """
    return rawobj.PolicyConfig("payload_limits", {"request": 100})


@pytest.fixture(scope="module")
def service(service):
    """
    Add the mapping rule to "/" endpoint using POST method
    """
    metric = service.metrics.create(rawobj.Metric("metric"))
    service.proxy.list().mapping_rules.create(rawobj.Mapping(metric, "/", "POST"))
    service.proxy.deploy()

    return service


@pytest.mark.parametrize("num_bytes,status_code", [(10, 200), (101, 413)])
def test_policy_limit_passing(api_client, num_bytes, status_code):
    """
    Tests that the request with a content_length greater than the limit
     will produce 413 status code
    - send a request containing the body of 'num_bytes' size
    - if num_bytes < RESPONSE_LIMIT assert 200
    - if num bytes > RESPONSE_LIMIT assert 413
    """
    data = random_string(num_bytes)
    client = api_client()

    # requests/urllib3 doesn't retry post(); need get() to wait until all is up
    client.get("/get")

    response = client.post("/post", data=data)
    assert response.status_code == status_code
