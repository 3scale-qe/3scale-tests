"""
Test for env variable APICAST_SERVICES_FILTER_BY_URL
"""

import pytest

from testsuite import rawobj
from testsuite.capabilities import Capability
from testsuite.utils import blame

pytestmark = [
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-1524"),
]


@pytest.fixture(scope="module")
def service_pass(request, service_proxy_settings, custom_service, lifecycle_hooks, backends_mapping):
    """Create custom service that should pass upon request"""
    service = custom_service(
        {"name": blame(request, "svc")}, service_proxy_settings, backends_mapping, hooks=lifecycle_hooks
    )
    yield service
    for usage in service.backend_usages.list():
        usage.delete()


@pytest.fixture(scope="module")
def application_pass(service_pass, custom_app_plan, custom_application, request, lifecycle_hooks):
    """Create custom application for 'service_pass'"""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service_pass)
    return custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)


@pytest.fixture(scope="module")
def api_client_pass(application_pass, api_client):
    """Create api_client for 'application_pass'"""
    return api_client(application_pass, disable_retry_status_list={404})


@pytest.fixture(scope="module")
def service_fail(request, service_proxy_settings, custom_service, lifecycle_hooks, backends_mapping):
    """Create custom service that should fail upon request"""
    service = custom_service(
        {"name": blame(request, "svc")}, service_proxy_settings, backends_mapping, hooks=lifecycle_hooks
    )
    yield service
    for usage in service.backend_usages.list():
        usage.delete()


@pytest.fixture(scope="module")
def application_fail(service_fail, custom_app_plan, custom_application, request, lifecycle_hooks):
    """Create custom application for 'service_fail'"""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service_fail)
    return custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)


@pytest.fixture(scope="module")
def api_client_fail(application_fail, api_client):
    """Create api_client for 'application_fail'"""
    return api_client(application_fail, disable_retry_status_list={404})


def test_filter_by_url(api_client_pass, api_client_fail, staging_gateway, service_pass):
    """
    Set apicast env variable 'APICAST_SERVICES_FILTER_BY_URL' to load only service_pass
    (APICAST_SERVICES_FILTER_BY_URL = Staging public base URL of service_pass)
    Request to 'service_pass' should return 200
    Request to 'service_fail' should return 404
    """
    public_url = f".*{service_pass.entity_id}-{staging_gateway.name}.*"
    staging_gateway.environ["APICAST_SERVICES_FILTER_BY_URL"] = public_url

    request = api_client_pass.get("/get")
    assert request.status_code == 200

    request = api_client_fail.get("/get")
    assert request.status_code == 404
