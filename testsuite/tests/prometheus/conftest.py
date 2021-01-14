"""Set of fixtures for Prometheus-related tests."""
import warnings

import pytest
import requests

from testsuite import prometheus


@pytest.fixture(scope="session", autouse=True)
def check_availability(prometheus_client):
    """
    Checks whether is the prometheus configured to run tests in this module.
    """
    try:
        if prometheus_client.get_metric("apicast_status") == []:
            warn_and_skip()
    except requests.exceptions.HTTPError:
        warn_and_skip()


def warn_and_skip():
    """
    Prints warning and skips the tests
    """
    warnings.warn("The testing of Prometheus scraping the metrics from APIcast has been skipped "
                  "as the Prometheus is not configured to do so.")
    pytest.skip("The Prometheus is not configured to run this test. The collectiong of basic metrics "
                "is not set up.")


@pytest.fixture(scope="session")
def prometheus_client(testconfig):
    """Returns an instance of Prometheus client."""
    return prometheus.PrometheusClient(testconfig["prometheus"]["url"])
