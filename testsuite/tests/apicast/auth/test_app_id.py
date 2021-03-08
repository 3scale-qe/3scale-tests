"""
Rewrite of spec/functional_specs/auth/app_id_spec.rb
"""
import pytest
from pytest_cases import parametrize_plus, fixture_ref, fixture_plus
from threescale_api.resources import Service

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest
from testsuite.capabilities import Capability
from testsuite.utils import blame

pytestmark = [pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY),
              pytest.mark.disruptive]


@pytest.fixture(scope="module")
def service_settings(service_settings):
    """Set auth mode to app_id/app_key"""
    service_settings.update({"backend_version": Service.AUTH_APP_ID_KEY})
    return service_settings


@pytest.fixture(scope="module")
def service_settings2(request):
    """settings for second service"""
    return {"name": blame(request, "svc"),
            "backend_version": Service.AUTH_APP_ID_KEY}


@pytest.fixture(scope="module")
def service2(backends_mapping, custom_service, service_settings2, service_proxy_settings, lifecycle_hooks):
    """Second service to test with"""
    return custom_service(service_settings2, service_proxy_settings, backends_mapping, hooks=lifecycle_hooks)


@pytest.fixture(scope="module")
def application2(service2, custom_application, custom_app_plan, lifecycle_hooks, request):
    """Application for second service"""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service2)
    return custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)


@fixture_plus(scope="module")
def client(application, prod_client):
    """
    Production client for first application. It won't redeploy gateway since it will be done in client2.
    The auth of the session is set up to none in order to test different auth params
    The auth of the request will be passed in test functions
    :param application: application
    :param prod_client: prod_client
    :return: production client
    """
    client = prod_client(app=application, redeploy=False)
    client.auth = None
    return client


# Client2 is calling a client in order to assure that the service was promoted
# and we can make the only single redeploy request
@fixture_plus(scope="module")
def client2(prod_client, application2, client):  # pylint: disable=unused-argument
    """
    Production client for second application.
    The auth of the session is set up to none in order to test different auth params
    The auth of the request will be passed in test functions
    :param application2: application2
    :param prod_client: prod_client
    :return: production client
    """
    client = prod_client(app=application2)
    client.auth = None
    return client


@fixture_plus(scope="module")
def app_id(application):
    """App id of first service"""
    return application["application_id"]


@fixture_plus(scope="module")
def app_key(application):
    """App key of first service"""
    return application.keys.list()["keys"][0]["key"]["value"]


@fixture_plus(scope="module")
def app_id2(application2):
    """App id of second service"""
    return application2["application_id"]


@fixture_plus(scope="module")
def app_key2(application2):
    """App key of second service"""
    return application2.keys.list()["keys"][0]["key"]["value"]


@parametrize_plus('test_client,application_id,key',
                  [(fixture_ref(client), fixture_ref(app_id), fixture_ref(app_key)),
                   (fixture_ref(client2), fixture_ref(app_id2), fixture_ref(app_key2))],
                  ids=["service_with_valid_credentials",
                       "service2_with_valid_credentials"])
def test_successful_requests(test_client, application_id, key):
    """Test checks if applications with correct auth params will return 200"""
    response = test_client.get('/get', params={"app_id": application_id, "app_key": key})
    assert response.status_code == 200

    echoed_request = EchoedRequest.create(response)
    assert echoed_request.params['app_key'] == key
    assert echoed_request.params['app_id'] == application_id


@parametrize_plus('test_client,application_id,key',
                  [(fixture_ref(client), fixture_ref(app_id2), fixture_ref(app_key2)),
                   (fixture_ref(client2), fixture_ref(app_id), fixture_ref(app_key)),
                   (fixture_ref(client), "", ""),
                   (fixture_ref(client), fixture_ref(app_id), ""),
                   (fixture_ref(client), "", fixture_ref(app_key))],
                  ids=["credentials_from_another_service",
                       "credentials_from_another_service",
                       "empty_id_and_key",
                       "empty_app_key",
                       "empty_app_id"])
def test_failed_requests(test_client, application_id, key):
    """Test checks if different invalid auth params returns 403 status code"""
    response = test_client.get('/get', params={"app_id": application_id, "app_key": key})
    assert response.status_code == 403
