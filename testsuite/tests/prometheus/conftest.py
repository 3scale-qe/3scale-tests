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
            warn_and_skip_apicast()
    except requests.exceptions.HTTPError:
        warn_and_skip_apicast()


def warn_and_skip_apicast():
    """
    Prints warning and skips the tests
    """
    warnings.warn("The testing of Prometheus scraping the metrics from APIcast has been skipped "
                  "as the Prometheus is not configured to do so.")
    pytest.skip("The Prometheus is not configured to run this test. The collectiong of basic metrics "
                "is not set up.")


@pytest.fixture(scope="session")
def prometheus_client(prometheus_url):
    """Returns an instance of Prometheus client."""
    return prometheus.PrometheusClient(prometheus_url)


@pytest.fixture(scope="session")
def prometheus_url(testconfig, openshift):
    """
    Returns an url of the Prometheus instance.
    Uses a route for the
    """
    if "prometheus" in testconfig:
        return testconfig["prometheus"]["url"]

    routes = openshift().routes.for_service('prometheus-operated')
    if len(routes) == 0:
        routes = openshift().routes.for_service('prometheus')

    if len(routes) == 0:
        warnings.warn("Prometheus is not present in this project. Prometheus tests have been skipped.")
        pytest.skip("Prometheus is not present in this project.")

    protocol = "https://" if "tls" in routes[0]["spec"] else "http://"
    return protocol + routes[0]['spec']['host']
