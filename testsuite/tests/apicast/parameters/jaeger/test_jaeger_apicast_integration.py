"""
Tests the apicast integration with jaeger, information about the requests
made through apicast is available in jaeger
It is necessary to have the jaeger url config value set
"""
import pytest

from testsuite.utils import randomize
from testsuite.capabilities import Capability

CAPABILITIES = [Capability.JAEGER]


# seems to fail everytime actually
@pytest.mark.flaky
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5669")
def test_jaeger_apicast_integration(api_client, jaeger, jaeger_randomized_name):
    """
    Makes a request to a random endpoint
    :param jaeger_randomized_name the identifying name of the service in jaeger
    Tests that:
     1) data from the jaeger contain a trace where with the http.url tag in the span
        with the '/' operationName has the value containing the randomized endpoint
     2) both the backend service url and original request uri are available as the jaeger tags
        "http.url" and "original_request_uri" respectively
    """
    endpoint = f"/anything/{randomize('random-endpoint')}"
    response = api_client().get(endpoint)
    assert response.status_code == 200

    traces = jaeger.traces(jaeger_randomized_name, "/")

    request_traced = False
    for trace in traces['data']:
        for span in trace['spans']:
            if span['operationName'] == '/':
                for tag in span['tags']:
                    if tag['key'] == "http.url" and endpoint in tag['value']:
                        request_traced = True
    assert request_traced

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
