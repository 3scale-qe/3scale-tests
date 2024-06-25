"""
Conftest for the backend listener prometheus tests
"""

import pytest
import requests

from testsuite.utils import warn_and_skip


@pytest.fixture(scope="session", autouse=True)
def check_availability(prometheus, backend_listener_url):
    """
    Checks whether is the prometheus configured to run tests in this module.
    """
    if not prometheus.has_metric(
        "apisonator_listener_response_codes",
        trigger_request=lambda: requests.get(f"{backend_listener_url}/transactions/authorize.xml"),
    ):
        warn_and_skip(
            "The Prometheus is not configured to run this test. The collection"
            " of basic metrics is not set up. The test has been skipped."
        )


@pytest.fixture(scope="session")
def backend_listener_url(testconfig):
    """
    Returns the url of the backend listener
    """
    return (
        f'{testconfig["threescale"]["backend_internal_api"]["route"]["spec"]["port"]["targetPort"]}'
        f'://{testconfig["threescale"]["backend_internal_api"]["route"]["spec"]["host"]}'
    )


@pytest.fixture(scope="module")
def service_token(application):
    """
    Returns the service token for the default service
    """
    return application.service.proxy.list().configs.list(env="sandbox")[0]["proxy_config"]["content"][
        "backend_authentication_value"
    ]


@pytest.fixture(scope="module")
def prometheus_response_codes_for_metric(prometheus):
    """
    Given a prometheus query, returns dict with response
    codes and counts associated with the response code
    """

    def response_codes_for_metric(key, labels):
        metric_response_codes = prometheus.get_metrics(key, labels)
        response_codes_count = {}
        for response_code_metric in metric_response_codes:
            response_codes_count[response_code_metric["metric"]["resp_code"]] = response_code_metric["value"][1]
        return response_codes_count

    return response_codes_for_metric
