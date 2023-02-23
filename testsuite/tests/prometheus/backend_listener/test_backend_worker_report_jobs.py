"""
When report request is sent to backend, the report job starts and
the report jobs metric in prometheus is increased.
"""

import pytest
import requests
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import


NUM_OF_REQUESTS = 10

pytestmark = [
    # can not be run in parallel
    pytest.mark.disruptive,
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-3176"),
    pytest.mark.skipif("TESTED_VERSION < Version('2.10')"),
]


@pytest.fixture(scope="module")
def auth_data(service, service_token, application):
    """
    Returns authentication data to be sent with the report
    transaction request
    """
    return {"service_token": service_token,
            "service_id": service.entity_id,
            "transactions[0][usage][hits]": "1",
            "transactions[0][user_key]": application.authobj().credentials["user_key"]
            }


@pytest.fixture(scope="module")
def prometheus_worker_job_count(prometheus):
    """
    Given a type of worker job (ReportJob or NotifyJob), returns the value of that metric
    """
    def _prometheus_worker_job_count(job_type):
        metric_response_codes = prometheus.get_metrics("apisonator_worker_job_count", {
                    "type": job_type
                })
        return int(metric_response_codes[0]['value'][1]) if len(metric_response_codes) > 0 else 0
    return _prometheus_worker_job_count


def test_authrep(backend_listener_url, auth_data, prometheus_worker_job_count, prometheus):
    """
    Sends NUM_OF_REQUESTS report requests on backend listener.

    Asserts that the metrics for the number of backend worker report jobs has increased
    by the number of requests sent.
    """
    # wait to update metrics triggered by previous tests
    prometheus.wait_on_next_scrape("backend-worker")

    report_jobs_count_before = prometheus_worker_job_count("ReportJob")

    for _ in range(NUM_OF_REQUESTS):
        response = requests.post(backend_listener_url + "/transactions.xml", data=auth_data)
        assert response.status_code == 202

    # wait for prometheus to collect the metrics
    prometheus.wait_on_next_scrape("backend-worker")

    report_jobs_count_after = prometheus_worker_job_count("ReportJob")

    assert report_jobs_count_after - report_jobs_count_before == NUM_OF_REQUESTS
