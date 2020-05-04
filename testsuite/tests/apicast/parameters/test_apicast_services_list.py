"""Rewrite of spec/openshift_specs/listed_apis_gateway_spec.rb

Test if apicast is able to serve requests only to listed services.
"""
import pytest
import requests

from testsuite import rawobj
from testsuite.gateways.gateways import Capability
from testsuite.utils import blame

pytestmark = pytest.mark.required_capabilities(Capability.APICAST, Capability.CUSTOM_ENVIRONMENT)


@pytest.fixture(scope="module")
def listed_service(service_proxy_settings, custom_service, request):
    """Create custom service to be listed."""
    return custom_service({"name": blame(request, "svc")}, service_proxy_settings)


@pytest.fixture(scope="module")
def listed_service_application(listed_service, custom_app_plan, custom_application, request):
    """Create custom application for listed service."""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), listed_service)
    return custom_application(rawobj.Application(blame(request, "app"), plan))


@pytest.fixture(scope="module")
def listed_service_client(listed_service, listed_service_application, staging_gateway):
    """Sets listed service to apicast."""
    client = listed_service_application.api_client()

    staging_gateway.set_env("APICAST_SERVICES_LIST", listed_service["id"])

    return client


@pytest.fixture
def api_client(application):
    """Sets session to api client for skipping retrying feature."""

    application.test_request()

    session = requests.Session()
    session.auth = application.authobj
    return application.api_client(session=session)


def test_listed_service_should_return_ok(listed_service_client):
    """Call to listed service should returns 200 OK."""
    assert listed_service_client.get("/get").status_code == 200


def test_not_listed_service_should_return_not_found(api_client):
    """Call to not listed service should returns 404 NotFound."""
    assert api_client.get("/get").status_code == 404
