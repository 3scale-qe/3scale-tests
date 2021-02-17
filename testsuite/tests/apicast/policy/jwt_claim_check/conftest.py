"""Conftest for jwt claim check policy"""
import pytest

from testsuite import rawobj
from testsuite.rhsso.rhsso import OIDCClientAuthHook
from testsuite.utils import blame


@pytest.fixture(scope="module", autouse=True)
def rhsso_setup(lifecycle_hooks, rhsso_service_info):
    """Have application/service with RHSSO auth configured"""

    lifecycle_hooks.append(OIDCClientAuthHook(rhsso_service_info))


@pytest.fixture(scope="module")
def application_doesnt_match(service, custom_application, custom_app_plan, lifecycle_hooks, request):
    """Second application that doesn't match jwt claim check policy"""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)
    application = custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)
    return application
