"""Rewrite of spec/prometheus_specs/apicast_metrics_spec.rb

Test metrics provided by apicast to Prometheus.
"""

import pytest
from packaging.version import Version

from testsuite import TESTED_VERSION

OPERATOR_SERVICE = ["threescale-operator-controller-manager-metrics-service"]


@pytest.mark.parametrize("service", OPERATOR_SERVICE)
def test_metrics_up(prometheus, service):
    """Operator metrics must contain "up" = "1"."""
    service = "threescale-operator-controller-manager-metrics-service"
    metrics = prometheus.get_metrics("up", labels={"service": service})[0]["value"][1]
    assert metrics == "1"


@pytest.mark.parametrize("service", OPERATOR_SERVICE)
def test_metrics_threescale_version(prometheus, service):
    """Metrics must contain metric named "threescale_version_info" containing 3scale version."""
    metrics = prometheus.get_metrics("threescale_version_info", labels={"service": service})[0]["metric"]["version"]
    assert Version(metrics) == TESTED_VERSION
