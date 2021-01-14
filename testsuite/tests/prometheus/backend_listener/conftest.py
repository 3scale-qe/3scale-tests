"""
Conftest for the backend listener prometheus tests
"""
import warnings
from time import sleep

import pytest
import requests

from testsuite.prometheus import PROMETHEUS_REFRESH


@pytest.fixture(scope="session", autouse=True)
def check_availability(prometheus_client, testconfig):
    """
    Checks whether is the prometheus configured to run tests in this module.
    """
    try:
        if prometheus_client.get_metric("apisonator_listener_response_codes") == []:
            # when testing on a new install, the metric does not have to be present
            url = f'{testconfig["threescale"]["backend_internal_api"]["route"]["spec"]["port"]["targetPort"]}' \
               f'://{testconfig["threescale"]["backend_internal_api"]["route"]["spec"]["host"]}' \
                  f'/transactions/authorize.xml'
            requests.get(url)

            # waits to refresh the prometheus metrics
            sleep(PROMETHEUS_REFRESH)

            if prometheus_client.get_metric("apisonator_listener_response_codes") == []:
                warn_and_skip()

    except requests.exceptions.HTTPError:
        warn_and_skip()


def warn_and_skip():
    """
    Prints warning and skips the tests
    """
    warnings.warn("The testing of Prometheus scraping the metrics from all pods has been skipped "
                  "as Prometheus is not configured to do so.")
    pytest.skip("The Prometheus is not configured to run this test. The scraping of metrics from all"
                "pods is not set up.")


@pytest.fixture(scope="session")
def backend_listener_url(testconfig):
    """
    Returns the url of the backend listener
    """
    return f'{testconfig["threescale"]["backend_internal_api"]["route"]["spec"]["port"]["targetPort"]}' \
           f'://{testconfig["threescale"]["backend_internal_api"]["route"]["spec"]["host"]}'


@pytest.fixture(scope="module")
def service_token(application):
    """
    Returns the service token for the default service
    """
    return application.service.proxy.list().configs.list(
        env="sandbox")[0]["proxy_config"]['content']["backend_authentication_value"]


@pytest.fixture(scope="module")
def prometheus_response_codes_for_metric(prometheus_client):
    """
    Given a prometheus query, returns dict with response
    codes and counts associated with the response code
    """
    def response_codes_for_metric(query):
        metric_response_codes = prometheus_client.get_metric(query)
        response_codes_count = dict()
        for response_code_metric in metric_response_codes:
            response_codes_count[response_code_metric['metric']['resp_code']] \
                = response_code_metric['value'][1]
        return response_codes_count

    return response_codes_for_metric
