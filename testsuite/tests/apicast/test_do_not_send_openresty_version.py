"""
Rewrite /spec/functional_specs/do_not_send_openresty_version_spec.rb

When requesting non existing endpoint openresty version should not be sent
in the response body or in the response header
"""
import backoff
import pytest
from testsuite import rawobj


@pytest.fixture(scope="module")
def service_proxy_settings():
    """Set backend url"""
    return rawobj.Proxy("https://echo-api.example.local")


@pytest.fixture(scope="module")
def client(api_client):
    """
    Client configured not to retry requests.

    By default, the failed requests are retried by the api_client.
    As 404 is the desired outcome of one of the tests, the client is
    configured not to retry requests to avoid long time execution.
    """
    return api_client(disable_retry_status_list={503, 404})


@backoff.on_predicate(
    backoff.fibo, lambda x: x.headers.get("server", "") not in ("openresty", "envoy"), max_tries=8, jitter=None)
def make_requests(client):
    """Make sure that we get 503 apicast (backend is not available)"""
    return client.get("/anything")


@pytest.mark.issue("https://issues.jboss.org/browse/THREESCALE-1989")
def test_do_not_send_openresty_version(client):
    """
    Make request to non existing endpoint
    Assert that the response does not contain openresty version in the headers
    Assert that the response does not contain openresty version in the body
    """
    response = make_requests(client)
    assert response.status_code == 503

    assert "server" in response.headers
    if response.headers["server"] == "envoy":
        pytest.skip("envoy edge proxy in use")
    assert response.headers["server"] == "openresty"

    assert "<center>openresty</center>" in response.text
