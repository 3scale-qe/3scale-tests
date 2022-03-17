"""
Tests the apicast integration with jaeger, information about the requests
made through apicast is available in jaeger
It is necessary to have the jaeger url config value set
"""
import backoff
import pytest

from testsuite.gateways.apicast.selfmanaged import SelfManagedApicast
from testsuite.utils import randomize
from testsuite.capabilities import Capability

CAPABILITIES = [Capability.JAEGER]


@pytest.fixture(scope="module")
def gateway_kind():
    """Gateway class to use for tests"""
    return SelfManagedApicast


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5669")
def test_jaeger_apicast_integration(api_client, jaeger, jaeger_service_name):
    """
    Makes a request to a random endpoint
    Tests that:
     1) data from the jaeger contain a trace where with the http.url tag in the span
        with the '/' operationName has the value containing the randomized endpoint
     2) both the backend service url and original request uri are available as the jaeger tags
        "http.url" and "original_request_uri" respectively
    """
    endpoint = f"/anything/{randomize('random-endpoint')}"
    response = api_client().get(endpoint)
    assert response.status_code == 200

    @backoff.on_predicate(backoff.fibo, lambda x: not x, 8, jitter=None)
    def request_traced():
        """Let's retry as the tracing might be 'lazy'"""
        traces = jaeger.traces(jaeger_service_name, "/")
        for trace in traces['data']:
            for span in trace['spans']:
                if span['operationName'] == '/':
                    for tag in span['tags']:
                        if tag['key'] == "http.url" and endpoint in tag['value']:
                            return True
        return False

    assert request_traced()

    traces = jaeger.traces(jaeger_service_name, "/")
    url_and_uri = True
    for trace in traces['data']:
        for span in trace['spans']:
            if span['operationName'] == '/':
                http_url = False
                original_request_uri = False
                for tag in span['tags']:
                    if tag['key'] == "http.url":
                        http_url = True
                    if tag['key'] == "original_request_uri":
                        original_request_uri = True
                url_and_uri = url_and_uri and http_url and original_request_uri
    assert url_and_uri
