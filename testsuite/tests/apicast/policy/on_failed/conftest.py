"""Default conftest for on_failed """

import pytest

from testsuite import rawobj
from testsuite.utils import blame


@pytest.fixture(params=[{}, {"error_status_code": 500}])
def on_failed_configuration(request) -> dict:
    """returns the configuration of the on_failed policy to use"""
    return request.param


@pytest.fixture
def failing_policy() -> dict:
    """returns the configuration of the on_failed policy to use"""
    return rawobj.PolicyConfig("failing", configuration={"fail_access": True}, version="0.1")


@pytest.fixture
def on_failed_policy(on_failed_configuration) -> dict:
    """returns the policy object with the specified configuration"""
    return rawobj.PolicyConfig("on_failed", on_failed_configuration)


@pytest.fixture
def service_settings(request) -> dict:
    "dict of service settings to be used when service created"
    return {"name": blame(request, "svc")}


# pylint: disable=too-many-arguments, too-many-instance-attributes
@pytest.fixture
def service(
    policy_settings, backends_mapping, custom_service, service_settings, service_proxy_settings, lifecycle_hooks
) -> dict:
    "Preconfigured service with backend defined existing over whole testsing session"
    svc = custom_service(service_settings, service_proxy_settings, backends_mapping, hooks=lifecycle_hooks)
    svc.proxy.list().policies.append(policy_settings)
    return svc


@pytest.fixture
def application(service, custom_application, custom_app_plan, lifecycle_hooks, request) -> dict:
    "application bound to the account and service existing over whole testing session"
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    app = custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)
    service.proxy.deploy()
    return app
