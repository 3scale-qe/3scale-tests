"""test special characters in Application description"""

import pytest

from testsuite import rawobj
from testsuite.capabilities import Capability
from testsuite.utils import blame

pytestmark = [pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY)]


@pytest.fixture(scope="module")
def app_plan(service, custom_app_plan, request):
    """Reuse application plan for all applications"""
    return custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)


@pytest.fixture(scope="module")
# pylint: disable=too-many-arguments
def application(description, service, custom_application, app_plan, lifecycle_hooks, request):
    "application bound to the account and service existing over whole testing session"
    plan = app_plan
    app_obj = rawobj.Application(blame(request, "app"), plan, description=description)
    app = custom_application(app_obj, hooks=lifecycle_hooks, annotate=description is None)
    service.proxy.deploy()
    return app


@pytest.fixture(scope="module")
def description(request):
    """Indirect fixture to set description"""
    return request.param


DESCRIPTIONS = (
    [None, "Simple text", "42"]
    + [pytest.param(f"{c}{n}", marks=[pytest.mark.fuzz]) for n, c in enumerate(r'!"#$%&\'()*+,-./\: ;<=>?@[]^`{|}~_')]
    + [pytest.param(f"{c}", marks=[pytest.mark.fuzz]) for n, c in enumerate(r'!"#$%&\'()*+,-./\: ;<=>?@[]^`{|}~_')]
    + [pytest.param(f"{n}{c}", marks=[pytest.mark.fuzz]) for n, c in enumerate(r'!"#$%&\'()*+,-./\: ;<=>?@[]^`{|}~')]
    + [
        pytest.param(
            "99_", marks=[pytest.mark.xfail, pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-10763")]
        )
    ]
)


@pytest.mark.parametrize(("description"), DESCRIPTIONS, indirect=True)
def test_successful_requests(api_client):
    """Test checks if applications was created and is functional"""
    response = api_client().get("/get")
    assert response.status_code == 200
