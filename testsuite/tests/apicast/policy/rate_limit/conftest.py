"""
Default conftest for rate limit tests
"""
import pytest
import pytest_cases

from testsuite import rawobj
from testsuite.utils import blame


@pytest.fixture
def service_settings(request):
    """dict of service settings to be used when service created"""
    return {"name": blame(request, "svc")}


@pytest.fixture
def policy_settings():
    """all has to be function-scoped in this namespace"""


@pytest_cases.fixture
def service_plus(custom_service, service_proxy_settings, request, policy_settings):
    """Usual service with policy_settings added to the policy_chain. function-scoped"""

    svc = custom_service({"name": blame(request, "svc")}, service_proxy_settings)
    if isinstance(policy_settings, dict):
        svc.proxy.list().policies.append(policy_settings)
    elif policy_settings is not None:
        svc.proxy.list().policies.append(*policy_settings)
    return svc


@pytest_cases.fixture
def application(service_plus, custom_app_plan, custom_application, request):
    """function-scoped application"""

    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service_plus)
    return custom_application(rawobj.Application(blame(request, "app"), plan))


@pytest_cases.fixture
def client(application):
    """function-scoped api_client

    Furthermore urllib3 has to be boosted to allow enough connections"""

    client = application.api_client()

    client.extend_connection_pool(500)
    yield client
    client.close()


@pytest_cases.fixture
def client2(application2):
    """
    Sets ssl_verify for api client
    """
    client = application2.api_client()
    yield client
    client.close()
