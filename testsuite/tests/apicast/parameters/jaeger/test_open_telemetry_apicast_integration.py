"""
Tests the apicast integration with jaeger, information about the requests
made through apicast is available in jaeger
It is necessary to have the jaeger url config value set
"""
import backoff
import pytest

from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import APICAST_OPERATOR_VERSION  # noqa # pylint: disable=unused-import
from testsuite.utils import randomize
from testsuite.capabilities import Capability

pytestmark = [pytest.mark.required_capabilities(Capability.JAEGER, Capability.CUSTOM_ENVIRONMENT)]


@pytest.mark.skipif("APICAST_OPERATOR_VERSION < Version('0.7.6')")
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7735")
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-9539")
def test_open_telemetry_apicast_integration(api_client, jaeger, jaeger_service_name):
    """
    Makes a request to a random endpoint
    Tests that:
     1) data from the jaeger contain a span with operation "apicast", where
        http.targer tag has the value containing the randomized endpoint
     2) original request uri is available as the jaeger tag "original_request_uri"
    """
    endpoint = f"/anything/{randomize('random-endpoint')}"
    response = api_client().get(endpoint)
    assert response.status_code == 200

    @backoff.on_predicate(backoff.fibo, lambda x: not x, max_tries=8, jitter=None)
    def request_traced():
        """Let's retry as the tracing might be 'lazy'"""
        traces = jaeger.traces(jaeger_service_name, "apicast")
        for trace in traces["data"]:
            for span in trace["spans"]:
                if span["operationName"] == "apicast":
                    for tag in span["tags"]:
                        if tag["key"] == "http.target" and endpoint in tag["value"]:
                            return True
        return False

    assert request_traced()

    traces = jaeger.traces(jaeger_service_name, "apicast")
    url_and_uri = True
    for trace in traces["data"]:
        for span in trace["spans"]:
            if span["operationName"] == "apicast":
                http_target = False
                original_request_uri = False
                for tag in span["tags"]:
                    if tag["key"] == "http.target" and endpoint in tag["value"]:
                        http_target = True
                    if tag["key"] == "original_request_uri" and endpoint in tag["value"]:
                        original_request_uri = True
                url_and_uri = url_and_uri and http_target and original_request_uri
    assert url_and_uri
