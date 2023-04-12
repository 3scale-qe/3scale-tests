"""Test for service discovery"""
import pytest

from testsuite import resilient
from testsuite.ui.views.admin.product.product import ProductNewView


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def service(login, navigator, threescale, testconfig, request):
    """Discover service in OpenShift"""
    view = navigator.navigate(ProductNewView)
    view.discover()

    service = resilient.resource_read_by_name(threescale.services, "tools-go-httpbin")

    yield service

    backend_id = service.backend_usages.list()[0]['backend_id']
    backend = threescale.backends.get(backend_id)
    backend.delete()
    service.delete()


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-8867")
@pytest.mark.flaky  # Due to attached issue this test will successfully pass only once in 5 minutes
@pytest.mark.sandbag  # Doesn't work on RHOAM
def test_service_discovery(api_client):
    """Test that discovered service can be used"""
    response = api_client().get("/get")
    assert response.status_code == 200
