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
def warmup_prod_gateway(prod_client):
    """Hit production apicast so that we can have metrics from it."""
    client = prod_client(redeploy=False)
    assert client.get("/status/200").status_code == 200


# pylint: disable=unused-argument
@pytest.fixture(scope="module", params=["3scale Apicast Staging", "3scale Apicast Production"])
def metrics(request, warmup_prod_gateway, prometheus_client):
    """Return all metrics from target defined of staging and also production apicast."""
    metrics = prometheus_client.get_metrics(request.param)
    return [m["metric"] for m in metrics["data"]]


@pytest.mark.parametrize("expected_metric", METRICS)
def test_metrics_from_target_must_contains_apicast_metrics(expected_metric, metrics):
    """Metrics must contains expected apicast metrics defined in METRICS."""
    assert expected_metric in metrics
