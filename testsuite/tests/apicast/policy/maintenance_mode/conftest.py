"Provides custom service to add policy to policy chain"

import pytest

import pytest_cases

from testsuite import rawobj
from testsuite.utils import blame
from testsuite.capabilities import Capability

pytestmark = [
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-6705"),
]


@pytest_cases.fixture
def status_code() -> int:
    """return the status code to check and test"""
    return 328


@pytest.fixture
def service_settings(request) -> dict:
    """dict of service settings to be used when service created"""
    return {"name": blame(request, "svc")}


@pytest.fixture
# pylint: disable=too-many-arguments
def service(
    policy_settings, backends_mapping, custom_service, service_settings, service_proxy_settings, lifecycle_hooks
):
    """Preconfigured service with backend defined existing over whole testsing session"""
    svc = custom_service(service_settings, service_proxy_settings, backends_mapping, hooks=lifecycle_hooks)
    svc.proxy.list().policies.append(policy_settings)
    return svc


@pytest.fixture
def application(service, custom_application, custom_app_plan, lifecycle_hooks, request) -> dict:
    """create a custom application plan with its application"""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    app = custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)
    service.proxy.deploy()
    return app
