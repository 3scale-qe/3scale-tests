"""Test for apicast pagination"""
import asyncio

import pytest

from testsuite.capabilities import Capability
from testsuite.utils import blame


# pylint: disable=too-many-arguments
@pytest.fixture(autouse=True)
async def many_services(request, custom_service, service_proxy_settings, lifecycle_hooks, custom_backend):
    """Creation of 500+ services"""
    backend_mapping = {"/": custom_backend("backend")}

    def _create_services():
        custom_service({"name": blame(request, "svc")}, service_proxy_settings, backend_mapping, hooks=lifecycle_hooks)

    return await asyncio.gather(
        *(asyncio.to_thread(_create_services) for _ in range(505))
    )


@pytest.mark.disruptive  # this generates high load on 3scale with impact on other tests
@pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-8373")
@pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT)
@pytest.mark.usefixtures("staging_gateway")
def test_apicast_pagination(api_client):
    """
    Preparation:
        - Create 500+ services
        - Create APICast
    Test:
        - Send request to the last created service
        - Assert that response status code is 200
    """
    client = api_client()
    response = client.get("/")
    assert response.status_code == 200
