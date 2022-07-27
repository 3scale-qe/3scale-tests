"""
When request is sent to system, requests metric in prometheus is increased.
"""

import pytest


METRICS_MASTER = [
    # new metrics introduced in THREESCALE-4743
    'rails_request_duration_seconds', 'rails_requests_total',
    'rails_view_runtime_seconds', 'rails_db_runtime_seconds',
    # existing metrics prior to THREESCALE-4743
    'sidekiq_enqueued_jobs', 'sidekiq_retry_jobs', 'sidekiq_queue_enqueued_jobs',
    'sidekiq_queue_max_processing_time_seconds', 'sidekiq_processed_jobs_total',
    'sidekiq_failed_jobs_total', 'sidekiq_workers',
    'sidekiq_processes', 'sidekiq_cron_jobs',
    'sidekiq_busy_workers', 'sidekiq_scheduled_jobs',
    'sidekiq_dead_jobs', 'sidekiq_queue_latency_seconds'
]

METRICS_SIDEKIQ = [
    'sidekiq_jobs_executed_total',
    'sidekiq_jobs_success_total',
    'sidekiq_job_runtime_seconds',
    'sidekiq_jobs_waiting_count',
    'sidekiq_jobs_scheduled_count',
    'sidekiq_jobs_retry_count',
    'sidekiq_jobs_dead_count',
    'sidekiq_active_processes',
    'sidekiq_active_workers_count',
    # TODO: test for this metrics after finding trigger for failed sidekiq job
    # 'sidekiq_jobs_failed_total'
]

pytestmark = [
    pytest.mark.sandbag,  # requires openshfit
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-4743"),
    pytest.mark.require_version("2.10"),
]


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def metrics_master(prometheus):
    """Return all metrics from target defined of system-master."""
    metrics = prometheus.get_metrics("system-master")
    return metrics


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def metrics_sidekiq(prometheus):
    """Return all metrics from target defined of system-master."""
    metrics = prometheus.get_metrics("system-sidekiq")
    return metrics


@pytest.mark.parametrize("metric", METRICS_MASTER)
def test_metric_master(metric, metrics_master):
    """ Test system_metrics metric. """
    assert metric in metrics_master


@pytest.mark.parametrize("metric", METRICS_SIDEKIQ)
def test_metric_sidekiq(metric, metrics_sidekiq):
    """ Test system_metrics metric. """
    assert metric in metrics_sidekiq
