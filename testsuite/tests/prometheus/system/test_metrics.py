"""
When request is sent to system, requests metric in prometheus is increased.
"""

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.prometheus import get_metrics_keys

METRICS_MASTER = [
    "rails_requests_total",
    "sidekiq_enqueued_jobs",
    "sidekiq_retry_jobs",
    "sidekiq_queue_enqueued_jobs",
    "sidekiq_processed_jobs_total",
    "sidekiq_failed_jobs_total",
    "sidekiq_workers",
    "sidekiq_processes",
    "sidekiq_cron_jobs",
    "sidekiq_busy_workers",
    "sidekiq_scheduled_jobs",
    "sidekiq_dead_jobs",
    "sidekiq_queue_latency_seconds",
    # most of the time its not set
    # 'sidekiq_queue_max_processing_time_seconds',
]

METRICS_DEVELOPER = [
    "rails_requests_total",
    # most of the time its not set
    # 'sidekiq_queue_max_processing_time_seconds'
]

METRICS_MASTER_HISTOGRAM = ["rails_request_duration_seconds"]

METRICS_SIDEKIQ = [
    "sidekiq_jobs_executed_total",
    "sidekiq_jobs_success_total",
    "sidekiq_jobs_waiting_count",
    "sidekiq_jobs_scheduled_count",
    "sidekiq_jobs_retry_count",
    "sidekiq_jobs_dead_count",
    "sidekiq_active_processes",
    "sidekiq_active_workers_count",
    # TODO: most of the time its not set, found out how to trigger
    # 'sidekiq_queue_max_processing_time_seconds',
    # TODO: test for this metrics after finding trigger for failed sidekiq job
    # 'sidekiq_jobs_failed_total',
]

METRICS_SIDEKIQ_HISTOGRAM = [
    "sidekiq_job_runtime_seconds",
]

pytestmark = [
    pytest.mark.sandbag,  # requires openshfit
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-4743"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-9934"),
    pytest.mark.skipif("TESTED_VERSION < Version('2.10')"),
]


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def metrics_master(prometheus):
    """Return all metrics from target defined of system-master."""
    metrics = get_metrics_keys(prometheus.get_metrics(labels={"container": "system-master"}))
    return metrics


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def metrics_developer(prometheus):
    """Return all metrics from target defined of system-master."""
    metrics = get_metrics_keys(prometheus.get_metrics(labels={"container": "system-developer"}))
    return metrics


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def metrics_sidekiq(prometheus):
    """Return all metrics from target defined of system-master."""
    metrics = get_metrics_keys(prometheus.get_metrics(labels={"container": "system-sidekiq"}))
    return metrics


@pytest.mark.parametrize("metric", METRICS_MASTER)
def test_metric_master(metric, metrics_master):
    """Test system_metrics metric."""
    assert metric in metrics_master


@pytest.mark.parametrize("metric", METRICS_MASTER_HISTOGRAM)
def test_metric_master_histogram(metric, metrics_master):
    """Test system_metrics metric."""
    for suffix in ["_bucket", "_sum", "_count"]:
        assert metric + suffix in metrics_master


@pytest.mark.parametrize("metric", METRICS_DEVELOPER)
def test_metric_developer(metric, metrics_developer):
    """Test system_metrics metric."""
    assert metric in metrics_developer


@pytest.mark.parametrize("metric", METRICS_SIDEKIQ)
def test_metric_sidekiq(metric, metrics_sidekiq):
    """Test sidekiq_metrics metric."""
    assert metric in metrics_sidekiq


@pytest.mark.parametrize("metric", METRICS_SIDEKIQ_HISTOGRAM)
def test_metric_sidekiq_histogram(metric, metrics_sidekiq):
    """Test sidekiq_metrics metric."""
    for suffix in ["_bucket", "_sum", "_count"]:
        assert metric + suffix in metrics_sidekiq
