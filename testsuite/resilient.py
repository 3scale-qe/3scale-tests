"""Helpers for reliable 3scale API calls (usually with retry)"""

import backoff


@backoff.on_exception(backoff.fibo, AssertionError, max_tries=8, jitter=None)
def analytics_list_by_service(threescale, service_id, metric_name, key, threshold=0):
    """Get usage stats for service"""
    value = threescale.analytics.list_by_service(service_id, metric_name=metric_name)[key]
    assert value >= threshold
    return value
