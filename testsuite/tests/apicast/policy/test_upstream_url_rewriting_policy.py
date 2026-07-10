"""
Rewrite spec/functional_specs/policies/upstream_apicast_url_rewrite_policy_spec.rb
"""

from urllib.parse import urlparse

import pytest

from testsuite import rawobj
from testsuite import resilient
from testsuite.echoed_request import EchoedRequest


@pytest.fixture(scope="module")
def upstream_url_one(private_base_url):
    """URL of the echo_api backend used as upstream for v1 rule"""
    return private_base_url("echo_api")


@pytest.fixture(scope="module")
def upstream_url_two(private_base_url):
    """URL of the httpbin backend used as upstream for v2 rule"""
    return private_base_url("httpbin")


@pytest.fixture(scope="module")
def service(service, upstream_url_one, upstream_url_two):
    """Add url_rewriting policy, configure metrics/mapping"""
    assert upstream_url_one != upstream_url_two, "Upstream rules must use different backends to verify routing"

    proxy = service.proxy.list()
    proxy.policies.insert(
        0,
        rawobj.PolicyConfig(
            "upstream",
            {
                "rules": [
                    {"url": upstream_url_one, "regex": "v1"},
                    {"url": upstream_url_two, "regex": "v2"},
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


def test_url_rewriting_policy_v1(api_client, upstream_url_one):
    """must rewrite /httpbin/v1 to /rewrite and get response from new domain echo-api.3scale.net"""
    parsed_url = urlparse(upstream_url_one)
    request = EchoedRequest.create(api_client().get("/httpbin/v1"))
    assert request.path == "/rewrite"
    assert request.headers["Host"] in (parsed_url.hostname, parsed_url.netloc)


def test_url_rewriting_policy_v2(api_client, application, upstream_url_two):
    """must rewrite /httpbin/v2 to /get and provide response from new domain httpbin"""
    parsed_url = urlparse(upstream_url_two)
    analytics = application.threescale_client.analytics
    old_usage = analytics.list_by_service(application["service_id"], metric_name="hits")["total"]
    response = api_client().get("/httpbin/v2")
    assert response.status_code == 200

    request = EchoedRequest.create(response)
    assert request.path == "/get"
    assert request.headers["Host"] in (parsed_url.hostname, parsed_url.netloc)

    hits = resilient.analytics_list_by_service(
        application.threescale_client, application["service_id"], "hits", "total", old_usage + 1
    )
    assert hits == old_usage + 1
