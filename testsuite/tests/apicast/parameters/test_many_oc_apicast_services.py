"""
Creates an amount (50) of services in openshift with a name starting with 'apicast'
Then asserts that the gateway has been correctly deployed.
"""
import pytest

from testsuite.gateways.gateways import Capability
from testsuite.openshift.client import ServiceTypes
from testsuite.utils import blame

pytestmark = [pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY),
              pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6315")]


@pytest.fixture(scope="module")
def service_names(request):
    """
    Generates a list of blamed service names.
    """
    names = []
    for i in range(50):
        names.append(f"apicast-{blame(request, str(i))}")
    return names


@pytest.fixture(scope="module")
def create_services(openshift, request, delete_services, service_names):
    """
    Creates services defined by the values from service_names.
    """
    openshift = openshift()
    request.addfinalizer(delete_services)

    for name in service_names:
        openshift.create_service(name, ServiceTypes.CLUSTER_IP, 8080, 8080)


@pytest.fixture(scope="module")
def delete_services(openshift, service_names):
    """
    Parametrized delete services function
    """
    openshift = openshift()

    def _delete_service():
        """
        Deletes the services defined by the service_names fixture.
        """
        for name in service_names:
            openshift.delete("service", name)

    return _delete_service


# pylint: disable=unused-argument
def test_apicast_deployed(create_services, api_client):
    """
    Sends a request using the newly deployed apicast.
    Asserts that the requests passes meaning the gateway deployed correctly.
    """
    request = api_client().get("/get")
    assert request.status_code == 200
