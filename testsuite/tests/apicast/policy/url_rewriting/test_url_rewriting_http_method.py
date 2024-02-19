"""
Tests that the rules in the url_rewriting_policy can match also against the
http method of the request.
"""

from packaging.version import Version  # noqa # pylint: disable=unused-import
import pytest
from testsuite.echoed_request import EchoedRequest
from testsuite import rawobj
from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import


pytestmark = [pytest.mark.skipif("TESTED_VERSION < Version('2.9')")]


@pytest.fixture(scope="module")
def service(service):
    """Add url_rewriting policy, configure metrics/mapping"""
    proxy = service.proxy.list()

    proxy.policies.insert(
        0,
        rawobj.PolicyConfig(
            "url_rewriting",
            {"commands": [{"op": "gsub", "regex": "initial", "replace": "rewritten", "methods": ["GET", "PUT"]}]},
        ),
    )

    metric = service.metrics.create(rawobj.Metric("get_metric"))
    hello_metric = service.metrics.create(rawobj.Metric("hello_metric"))

    proxy.mapping_rules.create(rawobj.Mapping(metric, pattern="/anything/rewritten", http_method="GET"))
    proxy.mapping_rules.create(rawobj.Mapping(metric, pattern="/anything/rewritten", http_method="PUT"))
    proxy.mapping_rules.create(rawobj.Mapping(metric, pattern="/anything/rewritten", http_method="POST"))
    proxy.mapping_rules.create(rawobj.Mapping(hello_metric, pattern="/anything/initial", http_method="POST"))

    # proxy needs to be updated to apply added mapping
    proxy.update(rawobj.Proxy())
    proxy.deploy()

    return service


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5259")
@pytest.mark.parametrize(
    "method,path_after,hits",
    [("GET", "/anything/rewritten", 1), ("PUT", "/anything/rewritten", 1), ("POST", "/anything/initial", 0)],
)
def test_url_rewriting_http_method(application, api_client, method, path_after, hits):
    """
    /initial should be rewritten to /rewritten on GET and PUT request, metrics should be counted
    the rule should not be matched on any other request method
    """
    analytics = application.threescale_client.analytics
    hits_before = analytics.list_by_service(application["service_id"], metric_name="get_metric")["total"]

    echoed_request = EchoedRequest.create(api_client().request(method=method, path="/anything/initial"))
    assert echoed_request.path == path_after

    hits_after = analytics.list_by_service(application["service_id"], metric_name="get_metric")["total"]

    assert hits_after - hits_before == hits
