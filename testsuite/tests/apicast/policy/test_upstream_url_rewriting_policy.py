"""
Rewrite spec/functional_specs/policies/upstream_apicast_url_rewrite_policy_spec.rb
"""

from urllib.parse import urlparse

import pytest

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def service(service, backend):
    """Add url_rewriting policy, configure metrics/mapping"""
    proxy = service.proxy.list()
    proxy.policies.insert(0, rawobj.PolicyConfig("upstream", {
        "rules": [{"url": backend("echo-api"), "regex": "v1"},
                  {"url": backend(), "regex": "v2"}]}))
    proxy.policies.append(rawobj.PolicyConfig("url_rewriting", {
        "commands": [{"op": "sub", "regex": "httpbin/v1", "replace": "rewrite"},
                     {"op": "sub", "regex": "httpbin/v2", "replace": "get"}]}))

    metric = service.metrics.create(
        {"name": "get_metric", "friendly_name": "get_metrics", "unit": "hit"})

    proxy.mapping_rules.create({
        "http_method": "GET", "pattern": "/",
        "metric_id": metric["id"], "delta": 1})

    # proxy needs to be updated to apply added mapping
    proxy.update()
    return service


def test_url_rewriting_policy_v1(api_client, backend):
    """must rewrite /httpbin/v1 to /rewrite and get response from new domain echo-api.3scale.net"""
    parsed_url = urlparse(backend("echo-api"))
    request = EchoedRequest.create(api_client.get("/httpbin/v1"))
    assert request.path == "/rewrite"
    assert request.headers["X-Forwarded-Host"] == parsed_url.hostname
    assert request.headers["X-Forwarded-Port"] == "443"
    assert request.headers["X-Forwarded-Proto"] == "https"


def test_url_rewriting_policy_v2(api_client, application, backend):
    """must rewrite /httpbin/v2 to /get and provide response from new domain httpbin"""
    parsed_url = urlparse(backend())
    analytics = application.threescale_client.analytics
    old_usage = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    response = api_client.get("/anything/anything")
    request = EchoedRequest.create(response)

    assert response.status_code == 200
    assert request.headers["Host"] == parsed_url.hostname

    hits = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    assert hits == old_usage + 1
