"""
rewrite ./spec/functional_specs/policies/retry_policy_spec.rb /

When making request to API with Retry policy, the request will retry until
success is achieved when:
    - the number of fail responses is less then the max number of retries
    - the number of fail responses is equal to the max number of retries
The request will fail when:
    - the number of fail responses is greater them the max number of retries
"""
import pytest
import requests
from testsuite import rawobj


@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url):
    """Have httpbin backend due to /fail-request implementation"""

    return rawobj.Proxy(private_base_url("httpbin"))


@pytest.fixture(scope="module")
def policy_settings():
    """Append the retry policy configured to 5 retries"""
    return rawobj.PolicyConfig("retry", {"retries": 5})


@pytest.fixture(scope="module")
def staging_gateway(staging_gateway):
    """Sets apicast env variable"""
    staging_gateway.environ["APICAST_UPSTREAM_RETRY_CASES"] = "http_500"
    return staging_gateway


@pytest.fixture(scope="module")
def api_client(application):
    """
    Client configured not to retry requests.

    By default, the failed requests are retried by the api_client.
    As 404 is the desired outcome of one of the tests, the client is
    configured not to retry requests to avoid long time execution.
    """
    # this will ensure all is up
    assert application.test_request().status_code == 200

    session = requests.Session()
    session.auth = application.authobj
    return application.api_client(session=session)


def reset_httpbin_endpoint(api_client):
    """Reset httpbin endpoint before each call by making request to
       /fail-request/0/200 endpoint"""
    api_client.get("/fail-request/0/200")


@pytest.mark.parametrize("num_of_requests, awaited_response", [
    pytest.param(4, 200, id="4 requests, should succeed"),
    pytest.param(5, 200, id="5 request should succeed"),
    pytest.param(6, 500, id="6 request, should fail")
])
def test_retry_policy(api_client, num_of_requests, awaited_response):
    """
    To test retry policy:
    - append the retry policy, conifgured to retry max n times
    - set apicast env variables APICAST_UPSTREAM_RETRY_CASES='http_500'
    - make requests using api_client, that is configured not to retry them automatically
    - before each request, reset the httpbin by making call to /fail-request/0/200
    - make request n-1 times (/fail-request/n-1/500)
    - test if response is 200
    - make request n times (/fail-request/n/500)
    - test if response is 200
    - make request n+1 times (/fail-request/n+1/500)
    - test if response is 500
    """
    reset_httpbin_endpoint(api_client)
    response = api_client.get(
        "/fail-request/" + str(num_of_requests) + "/500")
    assert response.status_code == awaited_response
