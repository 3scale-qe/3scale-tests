"""Set of fixtures for Prometheus-related tests."""
import pytest

from testsuite.utils import warn_and_skip


@pytest.fixture(scope="session", autouse=True)
def check_availability(prometheus):
    """
    Checks whether is the prometheus configured to run tests in this module.
    """

    if not prometheus.has_metric(
            "rails_requests_total"):
        warn_and_skip("The Prometheus is not configured to run this test. The collection"
                      " of basic metrics is not set up. The test has been skipped.")
