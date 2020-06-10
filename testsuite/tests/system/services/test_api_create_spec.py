"""
Rewrite spec/functional_specs/api_create_spec.rb
"""

import pytest
from testsuite import rawobj
from testsuite.utils import blame
from testsuite.gateways.gateways import Capability


@pytest.fixture(scope="module")
def service_settings(request):
    """
    Makes service with required name
    """
    return {"name": blame(request, "svc_")}


@pytest.fixture(scope="module")
def application(service, custom_application, custom_app_plan, lifecycle_hooks, request):
    """application bound to the account and service existing over whole testing session"""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    return custom_application(rawobj.Application(blame(request, "app_"), plan), hooks=lifecycle_hooks)


def test_contains(application, service_settings):
    """
    Checks if service name and application name contains "_".
    """
    assert "_" in application.service.entity['name']
    assert "_" in service_settings['name']


def test_api_client(api_client):
    """
    Test request has to pass and return HTTP 200 for staging client.
    """
    response = api_client.get('/get')
    assert response.status_code == 200


@pytest.mark.disruptive
@pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY)
def test_prod_client(prod_client):
    """
    Test request has to pass and return HTTP 200 for prod. client.
    """
    response = prod_client().get('/get')
    assert response.status_code == 200
