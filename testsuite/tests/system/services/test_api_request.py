"""
Rewrite spec/functional_specs/api_request_spec.rb
"""

import pytest

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest
from testsuite.utils import blame, randomize


@pytest.fixture(scope="module")
def service2(backends_mapping, custom_service, request, service_proxy_settings, lifecycle_hooks):
    """Second service to test with"""
    return custom_service(
        {"name": blame(request, "svc")}, service_proxy_settings, backends_mapping, hooks=lifecycle_hooks
    )


@pytest.fixture(scope="module")
def application2(service2, custom_application, custom_app_plan, lifecycle_hooks):
    """Second application to test with"""
    plan = custom_app_plan(rawobj.ApplicationPlan(randomize("AppPlan")), service2)
    return custom_application(rawobj.Application(randomize("App"), plan), hooks=lifecycle_hooks)


@pytest.fixture
def user_key2(application2):
    """User key for second application"""
    key = application2["user_key"]
    return key


@pytest.fixture
def user_key(application):
    """User key for application"""
    key = application["user_key"]
    return key


def test_first_service(api_client, user_key):
    """
    Test request has to pass and return HTTP 200 for staging client.
    Checks if user key for service matches.
    """
    response = api_client().get("/get")
    assert response.status_code == 200

    echoed_response = EchoedRequest.create(response)
    assert echoed_response.params.get("user_key") == user_key


def test_second_service(application2, api_client, user_key2):
    """
    Test request has to pass and return HTTP 200 for staging client.
    Checks if user key for second service matches.
    """
    api_client = api_client(application2)

    response = api_client.get("/get")
    assert response.status_code == 200

    echoed_response = EchoedRequest.create(response)
    assert echoed_response.params.get("user_key") == user_key2
