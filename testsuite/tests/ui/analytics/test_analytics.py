"""Add test for product and backend analytics"""

import pytest

from wait_for import wait_for, TimedOutError
from testsuite import rawobj
from testsuite.ui.views.admin.backend.analytics import BackendTrafficView
from testsuite.ui.views.admin.product.analytics import ProductTrafficView


@pytest.fixture(scope="module")
def backends_mapping(backend_anything, backend_valid):
    """
    Create 2 backend usages backends:
       - path to Backend 1: "/anything"
       - path to Backend 2: "/valid"
    """
    return {"/anything": backend_anything, "/valid": backend_valid}


@pytest.fixture(scope="module")
def backend_anything(custom_backend):
    """
    Create backend with mapping rule `/anything`
    """
    backend = custom_backend()
    metric = backend.metrics.list()[0]
    backend.mapping_rules.create(rawobj.Mapping(metric, "/anything"))
    return backend


@pytest.fixture(scope="module")
def backend_valid(custom_backend):
    """
    Create backend with mapping rule `/valid`
    """
    backend = custom_backend()
    metric = backend.metrics.list()[0]
    backend.mapping_rules.create(rawobj.Mapping(metric, "/valid"))
    return backend


@pytest.mark.usefixtures("login")
def test_analytics(navigator, service, api_client, backend_anything, backend_valid):
    """
    Test:
        - makes request to `/valid` endpoint
        - assert that value of product's hits is 1
        - makes request to `/anything/anything` endpoint
        - makes request to `/valid/valid` endpoint
        - assert that value of both backend's hits is 1
        - assert that value of product's hits is 5
    """
    api_client = api_client()
    api_client.get("/valid")

    traffic = navigator.navigate(ProductTrafficView, product=service)

    traffic.select_metric("hits")
    assert traffic.read_metric() == 1

    api_client.get("/anything/anything")
    api_client.get("/valid/valid")

    traffic.select_metric(f'hits.{service.backend_usages.list()[0]["backend_id"]}')
    assert traffic.read_metric() == 1

    traffic.select_metric(f'hits.{service.backend_usages.list()[1]["backend_id"]}')
    assert traffic.read_metric() == 1

    traffic.select_metric("hits")
    # Wait for the metric to update from initial value, then verify it's correct
    try:
        wait_for(lambda: traffic.read_metric() != 1, timeout="3s", delay=0.2)
    except TimedOutError:
        pass  # Metric didn't update after timeout, pytest assertion will fail
    assert traffic.read_metric() == 5

    traffic = navigator.navigate(BackendTrafficView, backend=backend_anything)

    traffic.select_metric(f"hits.{backend_anything.entity_id}")
    assert traffic.read_metric() == 1

    traffic = navigator.navigate(BackendTrafficView, backend=backend_valid)

    traffic.select_metric(f"hits.{backend_valid.entity_id}")
    assert traffic.read_metric() == 1
