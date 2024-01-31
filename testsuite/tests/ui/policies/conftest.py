"""Provides custom service and application to add policy to policy chain with function scope"""

import pytest

from testsuite import rawobj
from testsuite.utils import blame


@pytest.fixture()
def policy_service(request, backends_mapping, custom_service, service_proxy_settings, lifecycle_hooks):
    """Preconfigured service with backend with scope for 1 test due to harmful changes on policy chain"""
    return custom_service(
        {"name": blame(request, "svc")}, service_proxy_settings, backends_mapping, hooks=lifecycle_hooks
    )


@pytest.fixture()
def policy_application(policy_service, custom_application, custom_app_plan, lifecycle_hooks, request):
    """Application for for api calls with changed policy chain"""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), policy_service)
    app = custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)
    policy_service.proxy.deploy()
    return app
