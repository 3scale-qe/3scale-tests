"Rewrite spec/functional_specs/policies/default_credentials_spec.rb"

import pytest

from threescale_api.resources import Service

from testsuite import rawobj
from testsuite.utils import blame


@pytest.fixture(scope="module")
def application(application, service):
    "Application with default_credentials policy configured to use user_key"
    service.proxy.list().policies.insert(0, rawobj.PolicyConfig("default_credentials", {
        "auth_type": "user_key",
        "user_key": application["user_key"]}))

    return application


@pytest.fixture(scope="module")
def service_app_id_key(custom_service, service_proxy_settings, request):
    "Another service using app_id/key auth configuration"
    settings = {"name": blame(request, "CustSvc"), "backend_version": Service.AUTH_APP_ID_KEY}
    return custom_service(settings, service_proxy_settings)


@pytest.fixture(scope="module")
def application_app_id_key(custom_application, custom_app_plan, service_app_id_key, request):
    "Application with default_credentials policy configured to use app_id/key"
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "CustAPlan")), service_app_id_key)
    app = custom_application(rawobj.Application(blame(request, "CustApp"), plan))

    service_app_id_key.proxy.list().policies.insert(0, rawobj.PolicyConfig("default_credentials", {
        "auth_type": "app_id_and_app_key",
        "app_id": app["application_id"],
        "app_key": app.keys.list()["keys"][0]["key"]["value"]}))

    return app


@pytest.fixture(params=["application", "application_app_id_key"], ids=["user_key", "app_id_key"])
def a_client(request, api_client):
    "Helper to provide other fixtures as parameters"
    app = request.getfixturevalue(request.param)
    client = api_client(app)

    # now disable builtin auth credentials
    client.auth = None

    return client


def test_default_credentials(a_client):
    "test default_credentials behavior"
    assert a_client.get("/get").status_code == 200
