"""Test special characters in app_id and app_key"""

import pytest
from threescale_api.resources import Service

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest
from testsuite.capabilities import Capability
from testsuite.utils import blame

pytestmark = [pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY)]


@pytest.fixture(scope="module")
def service_settings(service_settings):
    """Have service with app_id/app_key pair authentication"""
    service_settings.update({"backend_version": Service.AUTH_APP_ID_KEY})
    return service_settings


@pytest.fixture(scope="module")
def app_plan(service, custom_app_plan, request):
    """Reuse application plan for all applications"""
    return custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)


@pytest.fixture(scope="module")
# pylint: disable=too-many-arguments
def application(app_id, app_key, service, custom_application, app_plan, lifecycle_hooks, request):
    "application bound to the account and service existing over whole testing session"
    plan = app_plan
    app_obj = rawobj.Application(blame(request, "app"), plan, app_id=app_id, app_key=app_key)
    app = custom_application(app_obj, hooks=lifecycle_hooks)
    service.proxy.deploy()
    return app


@pytest.fixture(scope="module")
def client2(application):
    """Client for a created application"""
    return application.api_client()


@pytest.fixture(scope="module")
def app_id(request):
    """indirect fixture for app_id used for creating and used as reference value in assert"""
    return request.param


@pytest.fixture(scope="module")
def app_key(request):
    """indirect fixture for app_key used for creating and used as reference value in assert"""
    return request.param


@pytest.mark.parametrize(
    ("app_id", "app_key"),
    [
        pytest.param("MYID", "keykey1"),
        pytest.param(
            "!#$&'(",
            "keykey2",
            marks=[
                pytest.mark.xfail,
                pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-9033"),
                pytest.mark.fuzz,
            ],
        ),
        pytest.param(
            ")*+,-./:",
            "keykey3",
            marks=[
                pytest.mark.xfail,
                pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-9033"),
                pytest.mark.fuzz,
            ],
        ),
        pytest.param(
            ";=?@",
            "keykey4",
            marks=[
                pytest.mark.xfail,
                pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-9033"),
                pytest.mark.fuzz,
            ],
        ),
        pytest.param(
            "_~",
            "keykey5",
            marks=[
                pytest.mark.xfail,
                pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-9033"),
                pytest.mark.fuzz,
            ],
        ),
        pytest.param(
            '"%<>[\\]^`{|}',
            "keykey6",
            marks=[
                pytest.mark.xfail,
                pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-10762"),
                pytest.mark.fuzz,
            ],
        ),
        pytest.param(
            "{}*~KEY",
            "keykey7",
            marks=[pytest.mark.xfail, pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-10761")],
        ),
        pytest.param(
            "9999_",
            "keykey8",
            marks=[
                pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-10763"),
                pytest.mark.fuzz,
            ],
        ),
    ],
    indirect=True,
)
def test_successful_requests(client2, app_id, app_key):
    """Test checks if applications was created and is functional"""
    response = client2.get("/")
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.params["app_key"] == app_key
    assert echoed_request.params["app_id"] == app_id
