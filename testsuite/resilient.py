"""Helpers for reliable 3scale API calls (usually with retry)"""

import logging
import time

import backoff

from threescale_api.errors import ApiClientError

log = logging.getLogger(__name__)


@backoff.on_exception(backoff.fibo, AssertionError, max_tries=8, jitter=None)
def analytics_list_by_service(threescale, service_id, metric_name, key, threshold=0):
    """Get usage stats for service"""
    value = threescale.analytics.list_by_service(service_id, metric_name=metric_name)[key]
    assert value >= threshold
    return value


@backoff.on_exception(backoff.fibo, AssertionError, max_tries=8, jitter=None)
def analytics_list_by_backend(threescale, backend_id, metric_name, key, threshold=0):
    """Get usage stats for service"""
    value = threescale.analytics.list_by_backend(backend_id, metric_name=metric_name)[key]
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


@backoff.on_exception(backoff.fibo, ApiClientError, max_tries=8, jitter=None)
def accounts_create(client, params):
    """
    Shortly after 3scale deployment or new tenant creation accounts.create can
    return error `Response(409 Conflict): b''`. Nevertheless the account seems
    created. This require special handling to ensure proper behavior as well as
    cleanup.
    """
    try:
        return client.accounts.create(params=params)
    except ApiClientError as err:
        if err.code == 409:
            client.accounts.delete(client.accounts.read_by_name(params["name"]).entity_id)
            time.sleep(2)
        raise err


@backoff.on_exception(backoff.fibo, ApiClientError, max_tries=8, jitter=None)
def proxy_update(svc, params):
    """Proxy update right after service create seems failing sometimes, let's give it bit more tries"""
    return svc.proxy.update(params=params)
