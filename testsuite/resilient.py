"""Helpers for reliable 3scale API calls (usually with retry)"""

import backoff


@backoff.on_exception(backoff.fibo, AssertionError, max_tries=8, jitter=None)
def stats_service_usage(threescale, service_id, metric_name, key, threshold=0):
    """Get usage stats for service"""
    value = threescale.analytics.list_by_service(service_id, metric_name=metric_name)[key]
    assert value >= threshold
    return value


@backoff.on_predicate(backoff.fibo, lambda x: x is None, max_tries=7, jitter=None)
def resource_read_by_name(object_instance, name: str):
    """
    Method add backoff function to read_by_name function of specified resource
    e.g. threescale. Should be used mainly in UI tests due to slower execution
    in UI vs API.
    @param object_instance: instance of the object e.g. threescale, threescale.backends
    @param name: Name of the specific resource to search for
    @return: Desired resource object
    """
    return object_instance.read_by_name(name)
