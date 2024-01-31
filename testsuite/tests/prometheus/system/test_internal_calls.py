"""
Test Prometheus metric for content_caching.
"""

import base64

import pytest
import requests

from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import TESTED_VERSION, rawobj  # noqa # pylint: disable=unused-import
from testsuite.prometheus import get_metrics_keys

pytestmark = [
    pytest.mark.disruptive,
    pytest.mark.flaky,
    pytest.mark.skipif("TESTED_VERSION < Version('2.10')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6446"),
]


@pytest.fixture(scope="session")
def backend_listener_url(testconfig):
    """
    Returns the url of the backend listener
    """
    return (
        f'{testconfig["threescale"]["backend_internal_api"]["route"]["spec"]["port"]["targetPort"]}'
        f'://{testconfig["threescale"]["backend_internal_api"]["route"]["spec"]["host"]}'
    )


@pytest.fixture(scope="session")
def backend_internal_api_token(testconfig):
    """
    Returns the token for the internal api.
    The token is 'username: password' encoded in base64, where username and password
    are defined in the backend-internal-api secret
    """
    return base64.b64encode(
        f'{testconfig["threescale"]["backend_internal_api"]["username"].decode("ascii")}:'
        f'{testconfig["threescale"]["backend_internal_api"]["password"].decode("ascii")}'.encode("ascii")
    ).decode("ascii")


@pytest.fixture(scope="module")
def auth_headers(backend_internal_api_token):
    """
    Authorization header for the backend internal api
    """
    return {"Authorization": f"Basic {backend_internal_api_token}"}


@pytest.mark.flaky
@pytest.mark.parametrize(
    "url",
    (
        "{}/internal/services/{}/stats",
        "{}/internal/services/{}/plans/{}/usagelimits",
        "{}/internal/services/{}/plans/{}/utilization",
    ),
)
def test_utilization(url, prometheus, application, backend_listener_url, auth_headers):
    """
    Test if cache works correctly and if prometheus contains content_caching metric.
    """

    # Wait so we have the latest data
    prometheus.wait_on_next_scrape("backend-worker")
    counts_before = extract_call_metrics(
        prometheus,
        "rails_requests_total",
        "system-provider",
        lambda x: x["metric"]["controller"].startswith("admin/api"),
    )

    service_id = application.service.entity_id
    app_plan_id = application.entity["plan_id"]
    requests.get(url.format(backend_listener_url, service_id, app_plan_id), verify=False, headers=auth_headers)

    # prometheus is downloading metrics periodicity, we need to wait for next fetch
    prometheus.wait_on_next_scrape("backend-worker")

    metrics = get_metrics_keys(prometheus.get_metrics(labels={"container": "system-provider"}))
    assert "rails_requests_total" in metrics

    counts_after = extract_call_metrics(
        prometheus,
        "rails_requests_total",
        "system-provider",
        lambda x: x["metric"]["controller"].startswith("admin/api"),
    )

    assert counts_after == counts_before


def extract_call_metrics(prometheus, query, container, predicate=None):
    """
    Given a prometheus query, returns dict with response
    codes and counts associated with the response code
    """
    metric_response_codes = prometheus.get_metrics(query, {"container": container})
    key_value_map = {}
    for response_code_metric in metric_response_codes:
        if predicate is None or predicate(response_code_metric):
            key_value_map[response_code_metric["metric"]["controller"]] = response_code_metric["value"][1]
    return key_value_map
