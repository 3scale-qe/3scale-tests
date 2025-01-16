"""Rewrite of spec/openshift_specs/listed_apis_gateway_spec.rb

Test if apicast is able to serve requests only to listed services.
"""

import pytest

from testsuite import rawobj
from testsuite.capabilities import Capability
from testsuite.utils import blame

pytestmark = pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT)


# pylint: disable=too-many-arguments
@pytest.fixture(scope="module")
def listed_service(service_proxy_settings, custom_service, request, lifecycle_hooks, staging_gateway, backends_mapping):
    """Create custom service to be listed

    Adds list of services to environment"""

    service = custom_service(
        {"name": blame(request, "svc")}, service_proxy_settings, backends_mapping, hooks=lifecycle_hooks
    )

    staging_gateway.environ["APICAST_SERVICES_LIST"] = service["id"]

    yield service
    for usage in service.backend_usages.list():
        usage.delete()


@pytest.fixture(scope="module")
def listed_service_application(listed_service, custom_app_plan, custom_application, request, lifecycle_hooks):
    """Create custom application for listed service."""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), listed_service)
    return custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)


@pytest.fixture(scope="module")
def listed_service_client(listed_service_application, api_client):
    """Sets listed service to apicast."""
    return api_client(listed_service_application)


@pytest.fixture(scope="module")
def client(application, api_client):
    """Sets session to api client for skipping retrying feature."""

    application.test_request()

    return api_client(disable_retry_status_list={404})


# initially this was designed in two separate tests, that didn't work as there
# was order dependency because of setup in listed_service_client, so either
# single selected execution or parallel run were failing
def test_apicast_services_list_param(listed_service_client, client):
    """Call to not listed service should returns 404 NotFound."""

    assert listed_service_client.get("/get").status_code == 200
    assert client.get("/get").status_code == 404
