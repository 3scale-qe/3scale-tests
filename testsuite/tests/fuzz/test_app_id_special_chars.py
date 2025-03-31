"""Test special characters in app_id and app_key"""

import random
import pytest
from threescale_api.resources import Service

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest
from testsuite.capabilities import Capability
from testsuite.utils import blame

pytestmark = [pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY)]


@pytest.fixture(scope="module")
def private_base_url(tools):
    """Change api_backend to httpbin for service."""

    def _private_base_url():
        return tools["httpbin"]

    return _private_base_url


@pytest.fixture(scope="module")
def service_proxy_settings(service_proxy_settings):
    "auth via url params doesn't work because of url encoding of special characters"
    service_proxy_settings.update(credentials_location="headers")
    return service_proxy_settings


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
def application(app_id, app_key, credentials_location, service, custom_application, app_plan, lifecycle_hooks, request):
    "application bound to the account and service existing over whole testing session"
    plan = app_plan
    app_obj = rawobj.Application(blame(request, "app"), plan, app_id=app_id, app_key=app_key)
    app = custom_application(app_obj, hooks=lifecycle_hooks)
    service.proxy.list().update({"credentials_location": credentials_location})
    service.proxy.deploy()
    return app


@pytest.fixture(scope="module")
def client2(application):
    """Client for a created application"""
    return application.api_client()


@pytest.fixture(scope="module")
def app_id(request):
    """indirect fixture for app_id used for creating and used as reference value in assert"""
    return "".join(random.sample(request.param, len(request.param)))


@pytest.fixture(scope="module")
def app_key(request):
    """indirect fixture for app_key used for creating and used as reference value in assert"""
    return request.param


@pytest.fixture(scope="module")
def credentials_location(request):
    """indirect fixture for credentials_location used for creating and used as reference value in assert"""
    return request.param


@pytest.mark.parametrize(
    ("app_id", "app_key", "credentials_location"),
    [
        # credentials located in the headers
        pytest.param("MYID", "keykey1", "headers"),
        pytest.param(
            "!#$&'(",
            "keykey2",
            "headers",
            marks=[
                pytest.mark.fuzz,
            ],
        ),
        pytest.param(
            ")*+,-./:",
            "keykey3",
            "headers",
            marks=[
                pytest.mark.fuzz,
            ],
        ),
        pytest.param(
            ";=?@",
            "keykey4",
            "headers",
            marks=[
                pytest.mark.fuzz,
            ],
        ),
        pytest.param(
            "_~ID",
            "keykey5",
            "headers",
            marks=[
                pytest.mark.fuzz,
            ],
        ),
        pytest.param(
            '"%<>[\\]^`{|}',
            "keykey6",
            "headers",
            marks=[
                pytest.mark.fuzz,
            ],
        ),
        pytest.param(
            "{}*~KEY",
            "keykey7",
            "headers",
            marks=[
                pytest.mark.fuzz,
            ],
        ),
        pytest.param(
            "9999_",
            "keykey8",
            "headers",
            marks=[
                pytest.mark.fuzz,
            ],
        ),
        # credentials located in the query
        pytest.param("MYID", "keykey1", "headers"),
        pytest.param(
            "!#$&'(",
            "keykey2",
            "query",
            marks=[
                pytest.mark.xfail,
                pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-10762"),
                pytest.mark.fuzz,
            ],
        ),
        pytest.param(
            ")*+,-./:",
            "keykey3",
            "query",
            marks=[
                pytest.mark.xfail,
                pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-10762"),
                pytest.mark.fuzz,
            ],
        ),
        pytest.param(
            ";=?@",
            "keykey4",
            "query",
            marks=[
                pytest.mark.xfail,
                pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-10762"),
                pytest.mark.fuzz,
            ],
        ),
        pytest.param(
            "_~ID",
            "keykey5",
            "query",
            marks=[
                pytest.mark.fuzz,
            ],
        ),
        pytest.param(
            '"%<>[\\]^`{|}',
            "keykey6",
            "query",
            marks=[
                pytest.mark.xfail,
                pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-10762"),
                pytest.mark.fuzz,
            ],
        ),
        pytest.param(
            "{}*~KEY",
            "keykey7",
            "query",
            marks=[
                pytest.mark.xfail,
                pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-10761"),
                pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-10762"),
                pytest.mark.fuzz,
            ],
        ),
        pytest.param(
            "9999_",
            "keykey8",
            "query",
            marks=[
                pytest.mark.fuzz,
            ],
        ),
    ],
    indirect=True,
)
def test_successful_requests(client2, app_id, app_key, credentials_location):
    """Test checks if applications was created and is functional"""
    response = client2.get("/get")
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    # import pdb; pdb.set_trace()
    if credentials_location == "headers":
        assert echoed_request.headers["app_key"] == app_key
        assert echoed_request.headers["app_id"] == app_id
    else:
        assert echoed_request.params["app_key"] == app_key
        assert echoed_request.params["app_id"] == app_id
