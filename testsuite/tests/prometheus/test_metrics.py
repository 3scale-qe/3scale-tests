"""Rewrite of spec/prometheus_specs/apicast_metrics_spec.rb

Test metrics provided by apicast to Prometheus.
"""
import pytest

from testsuite.gateways.gateways import Capability

pytestmark = [pytest.mark.flaky,
              pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY),
              pytest.mark.disruptive]


METRICS = [
    "nginx_error_log", "nginx_http_connections",
    "nginx_metric_errors_total", "openresty_shdict_capacity",
    "openresty_shdict_free_space", "threescale_backend_calls",
    "total_response_time_seconds", "upstream_response_time_seconds",
    "upstream_status",
]


@pytest.fixture(scope="module")
def client(prod_client):
    """Returns prod client instance."""
    client = prod_client(redeploy=False, promote=True)
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


# TODO: Remove pylint disable when pytest fixes problem, probably in 6.0.1
# https://github.com/pytest-dev/pytest/pull/7565
# pylint: disable=not-callable
@pytest.mark.parametrize("expected_metric", METRICS)
def test_metrics_from_target_must_contains_apicast_metrics(expected_metric, metrics):
    """Metrics must contains expected apicast metrics defined in METRICS."""
    assert expected_metric in metrics


def test_apicast_status_metrics(client, prometheus_client):
    """Test apicast_status metric.

    Apicast logs http status codes on prometheus as a counter.

    ISSUE: https://issues.redhat.com/browse/THREESCALE-5417
    """
    statuses = [300, 418, 507]

    for status in statuses:
        assert client.get(f"/status/{status}").status_code == status

    hits = prometheus_client.get_metric("apicast_status")

    hit_metrics = {status: int(hit["value"][1])
                   for status in statuses
                   for hit in hits
                   if int(hit["metric"]["status"]) == status}

    assert statuses == sorted(hit_metrics.keys())
    assert all([count > 0 for count in hit_metrics.values()])
