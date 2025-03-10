"""
Default conftest for rate limit tests
"""

import warnings
import pytest
import pytest_cases
import threescale_api.errors

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
def service_plus(custom_service, service_proxy_settings, request, policy_settings, backends_mapping):
    """Usual service with policy_settings added to the policy_chain. function-scoped"""

    svc = custom_service({"name": blame(request, "svc")}, service_proxy_settings, backends=backends_mapping)
    if isinstance(policy_settings, dict):
        svc.proxy.list().policies.append(policy_settings)
    elif policy_settings is not None:
        svc.proxy.list().policies.append(*policy_settings)
    yield svc
    for usage in svc.backend_usages.list():
        usage.delete()


@pytest_cases.fixture
def application(service_plus, custom_app_plan, custom_application, lifecycle_hooks, request):
    """function-scoped application"""

    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service_plus)
    return custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)


@pytest.fixture
def prod_client(production_gateway, application, request, testconfig):
    """
    Duplicate with different scope, the reasoning behind duplicate is that if called prod_client from root conftest
    it didn't behave as expected.
    Prepares application and service for production use and creates new production client

    Parameters:
        app (Application): Application for which create the client.
        promote (bool): If true, then this method also promotes proxy configuration to production.
        version (int): Proxy configuration version of service to promote.
        redeploy (bool): If true, then the production gateway will be reloaded

    Returns:
        api_client (HttpClient): Api client for application

    """

    def _prod_client(app=application, promote: bool = True, version: int = -1, redeploy: bool = True):
        if promote:
            if version == -1:
                version = app.service.proxy.list().configs.latest()["version"]
            try:
                app.service.proxy.list().promote(version=version)
            except threescale_api.errors.ApiClientError as err:
                warnings.warn(str(err))

        if redeploy:
            production_gateway.reload()

        client = app.api_client(endpoint="endpoint")
        if hasattr(client, "close"):
            if not testconfig["skip_cleanup"]:
                request.addfinalizer(client.close)
        return client

    return _prod_client


@pytest.fixture
def redis_url(tools, testconfig):
    """
    apicast "owned" redis to store global values

    Fixture is callable because of former implementation/interace

    """

    def _redis_url(scope):
        """if scope id 'global' returns URL, otherwise empty string"""
        if scope != "global":
            return ""
        try:
            redis = tools["apicast-testing-redis+svc:6379"]
            redis = redis.replace("http", "redis", 1)
            redis_url = f"{redis}/1"
        except KeyError:
            redis_url = testconfig["redis"]["url"]
        return redis_url

    return _redis_url


@pytest_cases.fixture
def client(application, prod_client):
    """
    Production client for first application.
    Furthermore urllib3 has to be boosted to allow enough connections
    """

    client = prod_client(application)

    client.extend_connection_pool(500)
    yield client
    client.close()


@pytest_cases.fixture
def client2(application2, prod_client):
    """
    Production client for second application.
    """

    client = prod_client(application2)
    yield client
    client.close()
