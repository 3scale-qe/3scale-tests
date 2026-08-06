"""Rewrite of spec/prometheus_specs/apicast_metrics_spec.rb

Test metrics provided by apicast to Prometheus.
"""

import pytest


@pytest.mark.xfail  # xfail because Apicast does not have default ServiceMonitor created
def test_metrics_up(prometheus, staging_gateway):
    """Operator metrics must contain "up" = "1"."""
    namespace = staging_gateway.openshift.project_name
    service = "apicast-operator-controller-manager-metrics-service"
    metrics = prometheus.get_metrics("up", labels={"namespace": namespace, "service": service})[0]["value"][1]
    assert metrics == "1"
