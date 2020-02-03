"""
Rewrite spec/functional_specs/policies/url_rewrite/url_rewrite_append_apicast_policy_spec.rb
"""

import pytest

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def service(service, backend):
    "Add url_rewriting policy, configure metrics/mapping"
    proxy = service.proxy.list()

    proxy.policies.append(rawobj.PolicyConfig("url_rewriting", {
        "commands": [{"op": "gsub", "regex": "hello", "replace": "get"}]}))

    metric = service.metrics.create(
        {"name": "get_metric", "friendly_name": "get_metrics", "unit": "hit"})

    proxy.mapping_rules.create({
        "http_method": "GET", "pattern": "/hello",
        "metric_id": metric["id"], "delta": 5})

    # proxy needs to be updated to apply added mapping
    proxy.update(rawobj.Proxy(backend("echo-api")))

    return service


def test_url_rewriting_hello(application, api_client):
    "/hello should be rewritten to /get, metrics should be counted"
    echoed_request = EchoedRequest.create(api_client.get("/hello"))
    assert echoed_request.path == "/get"

    analytics = application.threescale_client.analytics
    hits = analytics.list_by_service(application["service_id"], metric_name="get_metric")["total"]

    assert hits == 5


def test_url_rewriting_hello_world(api_client):
    "/hello_world should be rewritten to /get_world"
    echoed_request = EchoedRequest.create(api_client.get("/hello_world"))
    assert echoed_request.path == "/get_world"


def test_url_rewriting_hello_hello(api_client):
    "/hello_hello should be rewritten to /get_get"
    echoed_request = EchoedRequest.create(api_client.get("/hello_hello"))
    assert echoed_request.path == "/get_get"
