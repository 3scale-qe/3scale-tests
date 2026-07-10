"""Test special characters in app_id and app_key"""

import pytest
from threescale_api.resources import Service
from packaging.version import Version

from testsuite import TESTED_VERSION
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
    """auth via url params doesn't work because of url encoding of special characters"""
    service_proxy_settings.update(credentials_location="headers")
    return service_proxy_settings


@pytest.fixture(scope="module")
def service_settings(service_settings):
    """Have service with app_id/app_key pair authentication"""
    service_settings.update({"backend_version": Service.AUTH_APP_ID_KEY})
    return service_settings


@pytest.fixture(scope="module")
def app_plan_headers(service, custom_app_plan, request):
    """Reuse application plan for all headers applications"""
    return custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service)


# pylint: disable=too-many-arguments
@pytest.fixture()
def application_headers(app_id, app_key, custom_application, app_plan_headers, lifecycle_hooks, request):
    """Application with credentials sent via headers"""
    app_obj = rawobj.Application(blame(request, "app"), app_plan_headers, app_id=app_id, app_key=app_key)
    return custom_application(app_obj, hooks=lifecycle_hooks)


@pytest.fixture(scope="module")
def service_params(backends_mapping, custom_service, lifecycle_hooks, request):
    """Second service with credentials_location=query"""
    return custom_service(
        {"name": blame(request, "svc"), "backend_version": Service.AUTH_APP_ID_KEY},
        rawobj.Proxy(credentials_location="query"),
        backends_mapping,
        hooks=lifecycle_hooks,
    )


@pytest.fixture(scope="module")
def app_plan_params(service_params, custom_app_plan, request):
    """Reuse application plan for all params applications"""
    return custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service_params)


# pylint: disable=too-many-arguments
@pytest.fixture()
def application_params(app_id, app_key, custom_application, app_plan_params, lifecycle_hooks, request):
    """Application with credentials sent via query params"""
    app_obj = rawobj.Application(blame(request, "app"), app_plan_params, app_id=app_id, app_key=app_key)
    return custom_application(app_obj, hooks=lifecycle_hooks)


@pytest.fixture()
def app_id(request):
    """Indirect fixture for app_id used for creating application and as reference value in assert"""
    return request.param


@pytest.fixture()
def app_key(request):
    """Indirect fixture for app_key used for creating application and as reference value in assert"""
    return request.param


def _generate_params():
    """Generate test params for both headers and params credentials locations."""
    issue_10761 = pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-10761")
    issue_10762 = pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-10762")
    fuzz = pytest.mark.fuzz
    xfail = pytest.mark.xfail

    # (app_id, app_key, headers_marks, params_marks)
    _params = [
        ("MYID", "keykey1", [], []),
        ("!#$&'(", "keykey2", [fuzz], [fuzz, xfail, issue_10762]),
        (")*+,-./:", "keykey3", [fuzz], [fuzz, xfail, issue_10762]),
        (";=?@", "keykey4", [fuzz], [fuzz, xfail, issue_10762]),
        ("_~ID", "keykey5", [fuzz], [fuzz]),
        ('"%<>[\\]^`{|}', "keykey6", [fuzz], [fuzz, xfail, issue_10762]),
        ("{}*~KEY", "keykey7", [fuzz], [fuzz, xfail, issue_10761, issue_10762]),
        ("1111_", "keykey8", [fuzz], [fuzz]),
    ]

    params = []
    for app_id, app_key, marks, params_marks in _params:
        params.append(pytest.param(app_id, app_key, "headers", marks=marks))
        params.append(pytest.param(app_id, app_key, "params", marks=params_marks))
    return params


@pytest.mark.parametrize(
    ("app_id", "app_key", "credentials_location"),
    _generate_params(),
    indirect=["app_id", "app_key"],
)
def test_successful_requests(app_id, app_key, credentials_location, request):
    """Test checks if application was created and is functional"""
    application = request.getfixturevalue(f"application_{credentials_location}")
    client = application.api_client()

    response = client.get("/get")
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    creds = getattr(echoed_request, credentials_location)
    assert creds["app_key"] == app_key
    assert creds["app_id"] == app_id
