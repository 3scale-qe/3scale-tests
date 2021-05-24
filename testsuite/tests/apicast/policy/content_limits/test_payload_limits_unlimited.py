"""
Testing that the request/response content limit policy does not limit anything when using the
default value
"""
import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite.utils import random_string
from testsuite import rawobj, TESTED_VERSION # noqa # pylint: disable=unused-import

pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.10')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5244")]


@pytest.fixture(scope="module")
def policy_settings():
    """
    Enable the content limits policy with the default values (0)
    """
    return rawobj.PolicyConfig("payload_limits", {})


@pytest.fixture(scope="module")
def service(service):
    """
    Add the mapping rules as defined in the endpoints_and_methods fixture
    """
    metric = service.metrics.create(rawobj.Metric("metric"))
    service.proxy.list().mapping_rules.create(rawobj.Mapping(metric, "/", "POST"))
    service.proxy.deploy()

    return service


def test_policy_limit_passing(api_client):
    """
    - send a request with some data in body
    - assert response status code is 200
    """
    data = random_string(1000)
    client = api_client()

    # requests/urllib3 doesn't retry post(); need get() to wait until all is up
    client.get("/get")

    response = client.post('/post', data=data)
    assert response.status_code == 200


def test_payload_limits_response(api_client):
    """
    - send a request to the httpbin "/bytes/{num_bytes}" endpoint, that will produce a response
      containing a body of length 1000
    - assert that the response status code is 200
    """
    response = api_client().get("/bytes/1000")
    assert response.status_code == 200
