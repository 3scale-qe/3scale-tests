"""Rewrite of spec/prometheus_specs/apicast_metrics_spec.rb

Test metrics provided by apicast to Prometheus.
"""
import backoff
import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite.capabilities import Capability
from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import

pytestmark = [
    pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY),
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY),
    pytest.mark.disruptive,
]

METRICS = [
    # TODO: test for this metrics after finding trigger for nginx error
    # "nginx_error_log",
    "nginx_http_connections", "nginx_metric_errors_total", "openresty_shdict_capacity",
    "openresty_shdict_free_space", "threescale_backend_calls", "total_response_time_seconds",
    "upstream_response_time_seconds", "upstream_status",
]

STATUSES = [300, 418, 507]


# pylint: disable=unused-argument
@pytest.fixture(scope="module", params=["apicast-staging", "apicast-production"])
def metrics(request, prometheus):
    """Return all metrics from target defined of staging and also production apicast."""
    metrics = prometheus.get_metrics(request.param)
    return {m["metric"] for m in metrics["data"]}


# flaky as the testsuite does not trigger the metrics that are expected, their presence
# depends on prior usage of the gateway
@pytest.mark.flaky
@pytest.mark.parametrize("expected_metric", METRICS)
def test_metrics_from_target_must_contains_apicast_metrics(expected_metric, metrics):
    """Metrics must contains expected apicast metrics defined in METRICS."""
    assert expected_metric in metrics


# there is certain delay before all appears in Prometheus
@backoff.on_predicate(backoff.fibo, lambda x: sorted(x.keys()) != STATUSES, max_tries=8, jitter=None)
def apicast_status_metrics(prometheus, container):
    """Reliable gathering of prometheus metrics

    Metrics in prometheus appear with some delay, therefore retry is needed
    to ensure expected values are available"""
    hits = prometheus.get_metric("apicast_status")

    ret = {}
    for status in STATUSES:
        for hit in hits:
            if int(hit["metric"]["status"]) == status and hit["metric"]["container"] == container:
                ret[status] = int(hit["value"][1])
    return ret


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5417")
@pytest.mark.parametrize(("client", "container"), [("api_client", "apicast-staging"),
                                                   ("prod_client", "apicast-production")
                                                   ], )
def test_apicast_status_metrics(request, client, container, prometheus):
    """Test apicast_status metric.

    Apicast logs http status codes on prometheus as a counter.
    """

    client = request.getfixturevalue(client)
    client = client()

    for status in STATUSES:
        assert client.get(f"/status/{status}").status_code == status

    hit_metrics = apicast_status_metrics(prometheus, container)

    assert STATUSES == sorted(hit_metrics.keys())
    assert all(count > 0 for count in hit_metrics.values())
