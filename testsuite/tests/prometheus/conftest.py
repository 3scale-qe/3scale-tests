"""Set of fixtures for Prometheus-related tests."""
import pytest

from testsuite import prometheus


@pytest.fixture(scope="session")
def prometheus_client(testconfig):
    """Returns an instance of Prometheus client."""
    return prometheus.PrometheusClient(testconfig["prometheus"]["url"])
