"""
Rewrite spec/functional_specs/policies/url_rewrite/url_rewrite_prepend_before_apicast_policy_spec.rb
"""

import pytest

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def backend_default(private_base_url, custom_backend):
    """
    Default backend with url from private_base_url.
    Use 3scale echo-api as backend due to various URLs
    """
    return custom_backend("backend_default", endpoint=private_base_url("echo_api"))


@pytest.fixture(scope="module")
def service(service):
    "Add url_rewriting policy, configure metrics/mapping"
    proxy = service.proxy.list()

    proxy.policies.insert(
        0, rawobj.PolicyConfig("url_rewriting", {"commands": [{"op": "gsub", "regex": "hello", "replace": "get"}]})
    )

    metric = service.metrics.create(rawobj.Metric("get_metric"))

    proxy.mapping_rules.create({"http_method": "GET", "pattern": "/get", "metric_id": metric["id"], "delta": 5})

    # proxy needs to be updated to apply added mapping
    proxy.deploy()

    return service


def test_url_rewriting_hello(application, api_client):
    "/hello should be rewritten to /get, metrics should be counted"
    analytics = application.threescale_client.analytics
    hits_before = analytics.list_by_service(application["service_id"], metric_name="get_metric")["total"]

    echoed_request = EchoedRequest.create(api_client().get("/hello"))
    assert echoed_request.path == "/get"

    analytics = application.threescale_client.analytics
    hits_after = analytics.list_by_service(application["service_id"], metric_name="get_metric")["total"]

    assert hits_after == hits_before + 5


def test_url_rewriting_hello_world(api_client):
    "/hello_world should be rewritten to /get_world"
    echoed_request = EchoedRequest.create(api_client().get("/hello_world"))
    assert echoed_request.path == "/get_world"


def test_url_rewriting_hello_hello(api_client):
    "/hello_hello should be rewritten to /get_get"
    echoed_request = EchoedRequest.create(api_client().get("/hello_hello"))
    assert echoed_request.path == "/get_get"
