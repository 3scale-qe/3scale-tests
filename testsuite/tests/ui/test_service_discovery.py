"""Test for service discovery"""
import pytest

from testsuite import resilient
from testsuite.ui.views.admin.product.product import ProductNewView
from testsuite.utils import warn_and_skip


@pytest.fixture(scope="module", autouse=True)
def skip_rhoam(testconfig):
    """Service discovery requires special setup unavailable on RHOAM"""
    if testconfig["threescale"]["deployment_type"] == "rhoam":
        warn_and_skip(skip_rhoam.__doc__)


@pytest.fixture(scope="module")
def service(navigator, threescale, testconfig, request):
    """Discover service in OpenShift"""
    view = navigator.navigate(ProductNewView)
    view.discover()

    service = resilient.resource_read_by_name(threescale.services, "tools-go-httpbin")
    assert service, "Service wasn't created"

    if not testconfig["skip_cleanup"]:
        backend_id = service.backend_usages.list()[0]["backend_id"]
        backend = threescale.backends.get(backend_id)
        request.addfinalizer(backend.delete)
        request.addfinalizer(service.delete)
    return service


@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-8867")
@pytest.mark.flaky  # Due to attached issue this test will successfully pass only once in 5 minutes
@pytest.mark.sandbag  # Doesn't work on RHOAM
@pytest.mark.usefixtures("login")
def test_service_discovery(api_client):
    """Test that discovered service can be used"""
    response = api_client().get("/get")
    assert response.status_code == 200
