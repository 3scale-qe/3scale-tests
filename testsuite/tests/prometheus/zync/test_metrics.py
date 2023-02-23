"""
Check if all keys  are avaiable in Prometheus
"""

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.prometheus import get_metrics_keys

pytestmark = [
    pytest.mark.sandbag,  # requires openshift
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-4642"),
    pytest.mark.skipif("TESTED_VERSION < Version('2.10')"),
]

METRICS_QUE = [
    "que_job_enqueued_total",
    "que_job_failures_total",
    "que_job_performed_total",
    "que_job_retries_total",
    "que_jobs_scheduled_total",
    "que_workers_total",
    "rails_connection_pool_connections",
    "rails_connection_pool_size",
    "rails_connection_pool_waiting",
    "que_job_enqueued_total",
    "que_job_failures_total",
    "que_job_performed_total",
    "que_job_retries_total",
    "que_job_runtime_seconds_sum",
    "que_job_runtime_seconds_count",
]

METRICS_QUE_HISTOGRAM = [
    "que_job_duration_seconds",
]

METRICS_ZYNC = [
    "puma_backlog",
    "puma_max_threads",
    "puma_pool_capacity",
    "puma_running",
    # "puma_workers", starts at 2.11
    "rails_connection_pool_connections",
    "rails_connection_pool_size",
    "rails_connection_pool_waiting",
    "rails_requests_total",
]

METRICS_ZYNC_HISTOGRAM = [
    "rails_view_runtime_seconds",
    "rails_request_duration_seconds",
    "rails_db_runtime_seconds",
]


@pytest.fixture(scope="module")
def metrics_que(prometheus):
    """Return all metrics from target defined of zync-que."""
    return get_metrics_keys(prometheus.get_metrics(labels={"container": "que"}))


@pytest.fixture(scope="module")
def metrics_zync(prometheus):
    """Return all metrics from target defined of zync."""
    return get_metrics_keys(prometheus.get_metrics(labels={"container": "zync"}))


@pytest.mark.parametrize(("pod", "expected_metric"),
                         [("metrics_que", x) for x in METRICS_QUE] + [("metrics_zync", x) for x in METRICS_ZYNC]
                         )
def test_metric_zync(request, expected_metric, pod):
    """ Test metrics presence. """
    actual_metrics = request.getfixturevalue(pod)
    assert expected_metric in actual_metrics


@pytest.mark.parametrize(("pod", "expected_metric"),
                         [("metrics_que", x) for x in METRICS_QUE_HISTOGRAM] +
                         [("metrics_zync", x) for x in METRICS_ZYNC_HISTOGRAM]
                         )
def test_metric_zync_histogram(request, expected_metric, pod):
    """ Test metrics presence. """
    actual_metrics = request.getfixturevalue(pod)
    for suffix in ["_sum", "_count", "_bucket"]:
        assert expected_metric+suffix in actual_metrics
