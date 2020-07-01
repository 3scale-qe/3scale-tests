"""
Conftest for rate limit headers tests
"""

import pytest
from testsuite import rawobj
from testsuite.utils import blame


@pytest.fixture(scope="module")
def backend_usages(service):
    """
    Returns backends bound to the services.
    Should deliver slight performance improvement
    """
    return service.backend_usages.list()


@pytest.fixture(scope="module")
def application(service, app_plan, custom_application, request, lifecycle_hooks):
    """
    Creates application with a application plan defined in the app_plan fixture
    """
    proxy = service.proxy.list()

    application = custom_application(rawobj.Application(blame(request, "limited_app"), app_plan),
                                     hooks=lifecycle_hooks)

    proxy.update()

    return application


@pytest.fixture(scope="module")
def service(service):
    """
    Adds the rate_limit_headers policy to the service.
    Adds the caching policy set to none, so the caching is disabled and the remaining limits
    reported back are accurate
    """
    proxy = service.proxy.list()
    proxy.policies.insert(0, rawobj.PolicyConfig("rate_limit_headers", {}))
    proxy.policies.insert(0, rawobj.PolicyConfig("caching", {"caching_type": "none"}))
    return service
