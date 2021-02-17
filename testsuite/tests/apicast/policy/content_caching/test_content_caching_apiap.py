"""
Test valid content caching on product with multiple backends
"""
from packaging.version import Version  # noqa # pylint: disable=unused-import
import pytest

from testsuite import rawobj, TESTED_VERSION  # noqa # pylint: disable=unused-import
from testsuite.echoed_request import EchoedRequest
from testsuite.utils import randomize, blame

pytestmark = pytest.mark.skipif("TESTED_VERSION < Version('2.9')")


@pytest.fixture(scope="module")
def policy_settings():
    "config of cors policy"
    return rawobj.PolicyConfig("content_caching", {
        "rules": [{
            "cache": True,
            "header": "X-Cache-Status",
            "condition": {
                "combine_op": "and",
                "operations": [{
                    "left": "oo",
                    "op": "==",
                    "right": "oo"
                }]
            }
        }]
    })


@pytest.fixture(scope="module")
def backends_mapping(custom_backend, private_base_url):
    """
    Create 2 separate backends:
        - path to Backend 1: "/echo-api"
        - path to Backend 2: "/httpbin"
    """
    return {"/echo-api": custom_backend("backend_one", endpoint=private_base_url("echo_api")),
            "/httpbin": custom_backend("backend_two", endpoint=private_base_url("httpbin"))}


# pylint: disable=too-many-arguments
@pytest.fixture(scope="module")
def service2(backends_mapping, custom_service, service_proxy_settings, policy_settings, lifecycle_hooks, request):
    """Second service to test with"""
    svc = custom_service({"name": blame(request, "svc")}, service_proxy_settings, backends_mapping,
                         hooks=lifecycle_hooks)
    svc.proxy.list().policies.append(policy_settings)
    return svc


@pytest.fixture(scope="module")
def application2(service2, custom_application, custom_app_plan, lifecycle_hooks):
    """Second application to test with"""
    plan = custom_app_plan(rawobj.ApplicationPlan(randomize("AppPlan")), service2)
    return custom_application(rawobj.Application(randomize("App"), plan), hooks=lifecycle_hooks)


@pytest.fixture(scope="module")
def client(api_client):
    """
    Api client for the first service
    Apicast needs to load configuration in order to cache incomming requests
    """
    client = api_client()
    client.get("/echo-api/")
    return client


@pytest.fixture(scope="module")
def client2(application2, api_client):
    """
    Api client for the second service
    Apicast needs to load configuration in order to cache incomming requests
    """
    client = api_client(application2)
    client.get("/echo-api/")
    return client


@pytest.mark.parametrize('client_param', ('client', 'client2'), ids=["First service", "Second service"])
def test_caching_working_correctly(request, client_param):
    """
    Test that cache on works correctly with APIAP
    """
    api_client = request.getfixturevalue(client_param)

    response = api_client.get("/echo-api/working", headers=dict(origin="localhost"))
    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") != "HIT"

    for i in range(10):
        response = api_client.get("/echo-api/working", headers=dict(origin="localhost"))
        assert response.status_code == 200, "Request {} failed".format(i)
        assert response.headers.get("X-Cache-Status") == "HIT", "Request {} didn't hit the cache".format(i)


def test_other_service_cache(client, client2):
    """
    Test that cache of one product will not be used on the request of another product to the same backend
    """
    response = client.get("/echo-api/test", headers=dict(origin="localhost"))
    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") != "HIT"
    echoed_request = EchoedRequest.create(response)

    response = client.get("/echo-api/test", headers=dict(origin="localhost"))
    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") == "HIT"

    # another service should not hit the cache on same path and same backend
    response = client2.get("/echo-api/test", headers=dict(origin="localhost"))
    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") != "HIT"
    echoed_request2 = EchoedRequest.create(response)

    # Body of each response should be different
    assert echoed_request.json['uuid'] != echoed_request2.json['uuid']

    # Request to first service should be still cached
    response = client.get("/echo-api/test", headers=dict(origin="localhost"))
    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") == "HIT"


def test_other_backend_cache(client):
    """Test that cache of one backend will not be used on the request to another backend with the same path"""
    response = client.get("/echo-api/anything/test", headers=dict(origin="localhost"))
    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") != "HIT"

    response = client.get("/echo-api/anything/test", headers=dict(origin="localhost"))
    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") == "HIT"

    # another backend should not hit the cache of other backend on the same path
    response = client.get("/httpbin/anything/test", headers=dict(origin="localhost"))
    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") != "HIT"

    # Request to first backend should be still cached
    response = client.get("/echo-api/anything/test", headers=dict(origin="localhost"))
    assert response.status_code == 200
    assert response.headers.get("X-Cache-Status") == "HIT"
