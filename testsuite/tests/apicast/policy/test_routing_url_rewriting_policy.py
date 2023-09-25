"""
Rewrite spec/functional_specs/policies/combination/routing_url_rewrite_spec.rb
"""

from urllib.parse import urlparse

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
def service(service, private_base_url):
    """
    Set policy settings
    """
    proxy = service.proxy.list()
    proxy.policies.insert(
        0,
        {
            "name": "url_rewriting",
            "version": "builtin",
            "enabled": True,
            "configuration": {"commands": [{"op": "sub", "regex": "^/anything", "replace": "/get"}]},
        },
    )
    proxy.policies.insert(
        0,
        {
            "name": "routing",
            "version": "builtin",
            "enabled": True,
            "configuration": {
                "rules": [
                    {
                        "url": private_base_url("httpbin"),
                        "condition": {
                            "operations": [
                                {
                                    "liquid_value": "{{ original_request.path }}",
                                    "op": "matches",
                                    "value": "/anything",
                                    "match": "liquid",
                                }
                            ]
                        },
                    }
                ]
            },
        },
    )

    metric = service.metrics.create(rawobj.Metric("get_metric"))

    proxy.mapping_rules.create({"http_method": "GET", "pattern": "/get", "metric_id": metric["id"], "delta": 5})

    # proxy needs to be updated to apply added mapping
    proxy.deploy()
    return service


def test_routing_url_rewriting_policy_path_alpha(api_client):
    """
    Test for the request path send to /alpha to echo api
    """
    response = api_client().get("/alpha")
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.path == "/alpha"


def test_routing_url_rewriting_policy_path(api_client):
    """
    Test for the request path send to / to echo api
    """
    response = api_client().get("/")
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.path == "/"


def test_routing_url_rewriting_policy_path_anything(api_client, application, private_base_url):
    """
    Test for the route to httpbin and rewrite the path anything to get
    """
    analytics = application.threescale_client.analytics
    old_usage = analytics.list_by_service(application["service_id"], metric_name="get_metric")["total"]
    response = api_client().get("/anything")
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.headers["Host"] == urlparse(private_base_url("httpbin")).hostname
    hits = analytics.list_by_service(application["service_id"], metric_name="get_metric")["total"]
    assert hits == old_usage + 5
