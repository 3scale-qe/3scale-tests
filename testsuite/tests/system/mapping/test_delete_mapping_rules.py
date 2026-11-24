"""Test for https://issues.redhat.com/browse/THREESCALE-7112"""

import pytest
from threescale_api.errors import ApiClientError

from testsuite import rawobj


@pytest.fixture(scope="module")
def service(service):
    """Removes default mapping rule from service"""
    service.mapping_rules.list()[0].delete()
    service.proxy.deploy()
    return service


@pytest.fixture()
def methods(service):
    """Creates method for service"""
    hits = service.metrics.read_by_name("hits")
    method = hits.methods.create(rawobj.Method("method"))
    mapping = service.mapping_rules.create(rawobj.Mapping(method, "/anything"))
    return method, mapping


@pytest.fixture()
def metrics(service):
    """Creates metric for service"""
    metric = service.metrics.create(rawobj.Metric("metric"))
    mapping = service.mapping_rules.create(rawobj.Mapping(metric, "/anything"))
    return metric, mapping


@pytest.fixture(scope="module")
def backend(service, threescale):
    """Gets backend used by default service"""
    backend_id = service.backend_usages.list()[0]["backend_id"]
    return threescale.backends.read(backend_id)


@pytest.fixture()
def backend_methods(backend):
    """Creates method for backend"""
    hits = backend.metrics.list()[0]
    method = hits.methods.create(rawobj.Method("method"))
    mapping = backend.mapping_rules.create(rawobj.Mapping(method, "/anything"))
    return method, mapping


@pytest.fixture()
def backend_metrics(backend):
    """Creates metric for backend"""
    metric = backend.metrics.create(rawobj.Metric("metric"))
    mapping = backend.mapping_rules.create(rawobj.Mapping(metric, "/anything"))
    return metric, mapping


@pytest.mark.parametrize("methods_or_metrics", ["methods", "metrics", "backend_methods", "backend_metrics"])
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-7112")
@pytest.mark.nopersistence  # Test deletes method/metric hence test is not compatible with persistence plugin
def test_methods_and_metrics_with_mapping(request, service, api_client, methods_or_metrics):
    """
    Test:
        - Creates method/metric
        - Creates mapping rule for that method/metric
        - Assert that mapping rule is working
        - Assert that method/metric couldn't be deleted because it's used by mapping rule
        - Delete mapping rule
        - Delete method/metric

    """
    kind, mapping = request.getfixturevalue(methods_or_metrics)
    proxy = service.proxy.list()
    proxy.deploy()

    client = api_client(disable_retry_status_list={404})
    response = client.get("/anything")
    assert response.status_code == 200

    with pytest.raises(ApiClientError):
        kind.delete()

    mapping.delete()
    proxy.deploy()
    kind.delete()
