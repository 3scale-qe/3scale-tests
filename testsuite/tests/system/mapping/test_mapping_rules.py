"""
Rewrite:  spec/functional_specs/mapping_rules_spec.rb

When mapping rules are applied, the requests to mapped endpoints
with appropriate http method will succeed, the requests to not mapped
endpoints and the requests with inappropriate http method will fail
and return 404 response code or 403 if using WASMGateway

"""

import pytest
from testsuite import rawobj

pytestmark = pytest.mark.required_capabilities()


@pytest.fixture(scope="module")
def endpoints_and_methods():
    """
    Returns a list of tuples representing mappings to be set
    First value in the tuple is the mapped endpoint, the second value
    is the mapped http method
    """
    return {
        ("/ip", "GET"),
        ("/anything", "POST"),
        ("/delete", "DELETE"),
        ("/put", "PUT"),
        ("/patch", "PATCH"),
        ("/anything", "HEAD"),
        ("/anything", "OPTIONS"),
    }


@pytest.fixture(scope="module")
def service(service, endpoints_and_methods):
    """
    Add the mapping rules as defined in the endpoints_and_methods fixture
    """

    proxy = service.proxy.list()

    metric = service.metrics.create(rawobj.Metric("metric"))

    # delete implicit '/' rule
    proxy.mapping_rules.list()[0].delete()

    for url, method in endpoints_and_methods:
        proxy.mapping_rules.create(rawobj.Mapping(metric, pattern=url, http_method=method))

    proxy.deploy()

    return service


@pytest.fixture(scope="module")
def client(application, api_client):
    """
    Client configured not to retry requests.

    By default, the failed requests are retried by the api_client.
    As 404 is the desired outcome of one of the tests, the client is
    configured not to retry requests to avoid long time execution.
    """
    application.test_request()  # this will ensure all is up

    return api_client(disable_retry_status_list={404})


def test_mapping(client, endpoints_and_methods):
    """
    Make following request calls and assert they succeed:
        - GET request call to '/ip'
        - POST request call to '/anything'
        - DELETE request call to '/delete'
        - PUT request call to '/put'
        - PATCH request to '/patch'
        - HEAD request to '/anything'
        - OPTIONS request to '/anything'
        - POST request call to /anything/nonsense/foo
    Make following request calls and assert they fail with 404 http response:
        - POST request to GET mapping rule '/ip'
        - GET request to not existing endpoint '/imaginary'
    """

    for url, method in endpoints_and_methods:
        response = client.request(method=method, path=url)
        assert response.status_code == 200, (
            f"Unexpected status {response.status_code} from {method} request" f" to {url} endpoint"
        )

    response = client.post("/anything/nonsense/foo")
    assert response.status_code == 200

    response = client.post("/ip")
    assert response.status_code == 404
    assert "No Mapping Rule matched" in response.content.decode("utf8")

    response = client.get("/imaginary")
    assert response.status_code == 404
    assert "No Mapping Rule matched" in response.content.decode("utf8")
