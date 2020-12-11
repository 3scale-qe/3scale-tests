"""
Tests the analytics at the backend level
"""

import pytest
from packaging.version import Version  # noqa # pylint: disable=unused-import
from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import

pytestmark = [
    pytest.mark.skipif("TESTED_VERSION < Version('2.9')"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-3159")]


@pytest.fixture(scope="module")
def proxy(service):
    """
    Returns object representing proxy bound to a service.
    Should deliver slight performance improvement
    """
    return service.proxy.list()


@pytest.fixture(scope="module")
def backend_usages(service):
    """
    Returns backends bound to the services.
    Should deliver slight performance improvement
    """
    return service.backend_usages.list()


@pytest.fixture(scope="module")
def backend(threescale, backend_usages, proxy):
    """
    Creates mapping rule at the backend level associated with the backend default
    metric
    """
    backend = threescale.backends.read(backend_usages[0]["backend_id"])
    backend_metric = backend.metrics.list()[0]
    backend.mapping_rules.create(rawobj.Mapping(backend_metric, "/anything/get"))

    proxy.deploy()

    return backend


def test_analytics(application, api_client, backend):
    """
    Makes requests to endpoint mapped by the mapping rule of the backend.
    Gets the analytics of the backend.
    Asserts that the number of sent requests is the same as the number reported
    by analytics.
    """
    num_requests = 5

    for _ in range(num_requests):
        assert api_client.get("/anything/get").status_code == 200

    backend_metric = backend.metrics.list()[0]

    analytics = application.threescale_client.analytics
    hits_backed = analytics.list_by_backend(backend.entity_id,
                                            metric_name=backend_metric.entity_name)["total"]

    assert hits_backed == num_requests
