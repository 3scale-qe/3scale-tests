"Rewrite spec/functional_specs/policies/default_credentials_spec.rb"

import pytest

from threescale_api.resources import Service

from testsuite import rawobj
from testsuite.utils import randomize


@pytest.fixture(scope="module")
def application(application, service):
    "Application with default_credentials policy configured to use user_key"
    service.proxy.list().policies.insert(0, rawobj.PolicyConfig("default_credentials", {
        "auth_type": "user_key",
        "user_key": application["user_key"]}))

    return application


@pytest.fixture(scope="module")
def service_app_id_key(custom_service, service_proxy_settings):
    "Another service using app_id/key auth configuration"
    settings = {"name": randomize("CustomService"), "backend_version": Service.AUTH_APP_ID_KEY}
    return custom_service(settings, service_proxy_settings)


@pytest.fixture(scope="module")
def application_app_id_key(custom_application, custom_app_plan, service_app_id_key):
    "Application with default_credentials policy configured to use app_id/key"
    plan = custom_app_plan(rawobj.ApplicationPlan(randomize("CustomAppPlan")), service_app_id_key)
    app = custom_application(rawobj.Application(randomize("CustomApp"), plan))

    service_app_id_key.proxy.list().policies.insert(0, rawobj.PolicyConfig("default_credentials", {
        "auth_type": "app_id_and_app_key",
        "app_id": app["application_id"],
        "app_key": app.keys.list()["keys"][0]["key"]["value"]}))

    return app


@pytest.fixture(scope="module")
def api_client_app_id_key(application_app_id_key, testconfig):
    "client providing access to app with default_credentials using app_id/key"
    return application_app_id_key.api_client(verify=testconfig["ssl_verify"])


@pytest.fixture(params=["api_client", "api_client_app_id_key"], ids=["user_key", "app_id_key"])
def a_client(request):
    "Helper to provide other fixtures as parameters"
    client = request.getfixturevalue(request.param)
    # now disable builtin auth credentials
    client._session.auth = None  # pylint: disable=protected-access

    return client


def test_default_credentials(a_client):
    "test default_credentials behavior"
    assert a_client.get("/get").status_code == 200
