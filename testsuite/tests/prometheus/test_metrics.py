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
              pytest.mark.disruptive,
              ]

METRICS = [
    "nginx_error_log", "nginx_http_connections",
    "nginx_metric_errors_total", "openresty_shdict_capacity",
    "openresty_shdict_free_space", "threescale_backend_calls",
    "total_response_time_seconds", "upstream_response_time_seconds",
    "upstream_status",
]

STATUSES = [300, 418, 507]


@pytest.fixture(scope="module")
def client(prod_client):
    """Returns prod client instance."""
    client = prod_client()
    return client


@pytest.fixture(scope="module")
def warmup_prod_gateway(client):
    """Hit production apicast so that we can have metrics from it."""
    assert client.get("/status/200").status_code == 200


# pylint: disable=unused-argument
@pytest.fixture(scope="module", params=["3scale Apicast Staging", "3scale Apicast Production"])
def metrics(request, warmup_prod_gateway, prometheus_client):
    """Return all metrics from target defined of staging and also production apicast."""
    metrics = prometheus_client.get_metrics(request.param)
    return [m["metric"] for m in metrics["data"]]


# flaky as the testsuite does not trigger the metrics that are expected, their presence
# depends on prior usage of the gateway
@pytest.mark.flaky
@pytest.mark.parametrize("expected_metric", METRICS)
def test_metrics_from_target_must_contains_apicast_metrics(expected_metric, metrics):
    """Metrics must contains expected apicast metrics defined in METRICS."""
    assert expected_metric in metrics


# there is certain delay before all appears in Prometheus
@backoff.on_predicate(backoff.fibo, lambda x: sorted(x.keys()) == STATUSES, 8, jitter=None)
def apicast_status_metrics(prometheus):
    """Reliable gathering of prometheus metrics

    Metrics in prometheus appear with some delay, therefore retry is needed
    to ensure expected values are available"""
    hits = prometheus.get_metric("apicast_status")

    return {
        status: int(hit["value"][1]) for status in STATUSES for hit in hits if int(hit["metric"]["status"]) == status}


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-5417")
def test_apicast_status_metrics(client, prometheus_client):
    """Test apicast_status metric.

    Apicast logs http status codes on prometheus as a counter.
    """

    for status in STATUSES:
        assert client.get(f"/status/{status}").status_code == status

    hit_metrics = apicast_status_metrics(prometheus_client)

    assert STATUSES == sorted(hit_metrics.keys())
    assert all(count > 0 for count in hit_metrics.values())
