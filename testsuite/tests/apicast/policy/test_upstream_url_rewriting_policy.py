"""
Rewrite spec/functional_specs/policies/upstream_apicast_url_rewrite_policy_spec.rb
"""

from urllib.parse import urlparse

import pytest

from testsuite import rawobj, resilient
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def service(service, private_base_url):
    """Add url_rewriting policy, configure metrics/mapping"""
    proxy = service.proxy.list()
    proxy.policies.insert(
        0,
        rawobj.PolicyConfig(
            "upstream",
            {
                "rules": [
                    {"url": private_base_url("echo_api"), "regex": "v1"},
                    {"url": private_base_url(), "regex": "v2"},
                ]
            },
        ),
    )
    proxy.policies.append(
        rawobj.PolicyConfig(
            "url_rewriting",
            {
                "commands": [
                    {"op": "sub", "regex": "httpbin/v1", "replace": "rewrite"},
                    {"op": "sub", "regex": "httpbin/v2", "replace": "get"},
                ]
            },
        )
    )

    metric = service.metrics.create({"name": "get_metric", "friendly_name": "get_metrics", "unit": "hit"})

    proxy.mapping_rules.create({"http_method": "GET", "pattern": "/", "metric_id": metric["id"], "delta": 1})

    # proxy needs to be updated to apply added mapping
    proxy.deploy()
    return service


def test_url_rewriting_policy_v1(api_client, private_base_url):
    """must rewrite /httpbin/v1 to /rewrite and get response from new domain echo-api.3scale.net"""
    parsed_url = urlparse(private_base_url("echo_api"))
    request = EchoedRequest.create(api_client().get("/httpbin/v1"))
    assert request.path == "/rewrite"
    # X-Forwarded- can contain more values
    assert parsed_url.hostname in request.headers["X-Forwarded-Host"]
    assert "443" in request.headers["X-Forwarded-Port"]
    assert "https" in request.headers["X-Forwarded-Proto"]


def test_url_rewriting_policy_v2(api_client, application, private_base_url):
    """must rewrite /httpbin/v2 to /get and provide response from new domain httpbin"""
    parsed_url = urlparse(private_base_url())
    analytics = application.threescale_client.analytics
    old_usage = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    response = api_client().get("/anything/anything")
    assert response.status_code == 200

    request = EchoedRequest.create(response)
    assert request.headers["Host"] == parsed_url.hostname

    hits = resilient.analytics_list_by_service(
        application.threescale_client, application["service_id"], "hits", "total", old_usage + 1
    )
    assert hits == old_usage + 1
