"""Set of fixtures for Prometheus-related tests."""
import pytest

from testsuite.utils import warn_and_skip


@pytest.fixture(scope="module", autouse=True)
def check_availability(api_client, prod_client, prometheus):
    """
    Checks whether is the prometheus configured to run tests in this module.
    """

    if not prometheus.has_metric(
            "apicast_status",
            lambda: (api_client.get('/anything'), prod_client.get('/anything'))):
        warn_and_skip("The Prometheus is not configured to run this test. The collection"
                      " of basic metrics is not set up. The test has been skipped.")
