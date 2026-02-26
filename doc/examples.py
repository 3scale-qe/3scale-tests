"""
This is complication of examples how to use testsuite and write tests. As such
this is not supposed to be executed and it isn't goal to have this executable
"""
from testsuite.gateways import SelfManagedApicast, TemplateApicast, gateway
from testsuite.capabilities import Capability
from testsuite.rhsso import OIDCClientAuth
from threescale_api.resources import Service
import pytest
from testsuite import rawobj


################################################################################
# run simple test
# See: https://github.com/3scale-qe/3scale-tests/blob/v2.16.0.8/testsuite/tests/apicast/policy/retry_policy/test_retry_policy.py#L59
from testsuite.utils import blame


def test_basic_request(application):
    """test request has to pass and return HTTP 200"""
    assert application.test_request().status_code == 200
    assert application.test_request("/anything").status_code == 200


# or use api_client
# See: https://github.com/3scale-qe/3scale-tests/blob/v2.16.0.8/testsuite/tests/apicast/apiap/test_routing_policy_order.py#L40
def test_another_basic_request(api_client):
    """test requests have to pass and return HTTP 200"""
    client = api_client()
    assert client.get("/get").status_code == 200
    assert client.get("/get", params={"arg": "value"})
    assert client.post("/post", data={"arg": "value"}, headers={"X-Custom-Header": "value"})


################################################################################
# to add policy use policy_settings fixture.
# BEWARE! This is defined in testsuite/tests/apicast/policy/conftest.py
# See: https://github.com/3scale-qe/3scale-tests/blob/v2.16.0.8/testsuite/tests/apicast/parameters/policies/conftest.py#L7
@pytest.fixture(scope="module")
def policy_settings():
    """Have service with upstream_connection policy added to the chain and
    configured to read_timeout after 5 seconds"""
    return rawobj.PolicyConfig("upstream_connection", {"read_timeout": 5})


# to add multiple policies you can return them in the list
# See: https://github.com/3scale-qe/3scale-tests/blob/v2.16.0.8/testsuite/tests/apicast/parameters/test_policy_dependency.py#L92
@pytest.fixture(scope="module")
def policy_settings():
    """Have service with upstream_connection policy added to the chain and
    configured to read_timeout after 5 seconds"""
    return [rawobj.PolicyConfig("upstream_connection", {"read_timeout": 5}), rawobj.PolicyConfig("fapi", {})]


# if you need to add policy before default 3scale APIcast policy you need to apply different approach
# See: https://github.com/3scale-qe/3scale-tests/blob/v2.16.0.8/testsuite/tests/apicast/apiap/test_routing_policy_order.py#L28
@pytest.fixture(scope="module")
def service(service):
    """
    Set upstream connection before 3scale APIcast
    """
    service.proxy.list().policies.insert(0, rawobj.PolicyConfig("upstream_connection", {"read_timeout": 5}))
    return service


################################################################################
# To switch authentication define two following fixtures
# See: https://github.com/3scale-qe/3scale-tests/blob/v2.16.0.8/testsuite/tests/apicast/auth/test_app_id.py#L21
@pytest.fixture(scope="module")
def service_settings(service_settings):
    """Have service with app_id/app_key pair authentication"""
    service_settings.update({"backend_version": Service.AUTH_APP_ID_KEY})
    return service_settings


# See: https://github.com/3scale-qe/3scale-tests/blob/v2.16.0.8/testsuite/tests/apicast/auth/test_headers_user_key.py#L22
@pytest.fixture(scope="module")
def service_proxy_settings(service_proxy_settings):
    """Expect credentials to be passed in headers"""
    service_proxy_settings.update({"credentials_location": "headers"})
    return service_proxy_settings


###############################################################################
# To test call against production gateway you can use the prod_client fixture which promotes the configuration to
# production and then creates the actual client
# (default value of the version is 1)
# See: https://github.com/3scale-qe/3scale-tests/blob/v2.16.0.8/testsuite/tests/apicast/parameters/apicast_path_routing/test_apicast_service_oidc.py#L86

# If you don't need to promote a specific version you can use it like this (the default version promoted is 1)
@pytest.mark.disruptive  # test should be mark as disruptive because of production gateway redeploy
@pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY)  # Test should have mark that states that it needs production_gateway
def test_production_call(application, prod_client):
    client = prod_client(application)
    response = client.get("/get")


# or you can specify the version yourself
@pytest.mark.disruptive  # test should be mark as disruptive because of production gateway redeploy
@pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY)  # Test should have mark that states that it needs production_gateway
def test_version_production_call(application, prod_client):
    client = prod_client(application, version=3)
    response = client.get("/get")


# you can also create production client without promoting the configuration or redeploying the gateway
@pytest.mark.disruptive  # test should be mark as disruptive because of production gateway redeploy
@pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY)  # Test should have mark that states that it needs production_gateway
def test_production_call_without_promote(application, prod_client):
    client = prod_client(application, promote=False)
    response = client.get("/get")


@pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY)  # Test should have mark that states that it needs production_gateway
def test_production_call_without_redeploy(application, prod_client):
    client = prod_client(application, redeploy=False)
    response = client.get("/get")

###############################################################################
# When requiring specific backend to be used, override the backend_default fixture
# See: https://github.com/3scale-qe/3scale-tests/blob/v2.16.0.8/testsuite/tests/apicast/parameters/http_proxy/test_http_proxy.py#L15
@pytest.fixture(scope="module")
def backend_default(private_base_url, custom_backend):
    """Use echo_api as the backend for this test module"""
    return custom_backend("backend_default", endpoint=private_base_url("echo_api"))


###############################################################################
# To configure metrics mapping rules, insert following into the service fixture
# See: https://github.com/3scale-qe/3scale-tests/blob/v2.16.0.8/testsuite/tests/apicast/test_limit_exceeded_metric.py#L21
@pytest.fixture(scope="module")
def service(service):
    proxy = service.proxy.list()

    metric = service.metrics.create(rawobj.Metric("name_foo"))
    proxy.mapping_rules.create(rawobj.Mapping(metric, pattern="/foo"))

    # proxy needs to be updated to apply added mapping
    proxy.update()
    return service


###############################################################################
# To explicitly specify gateway for tests override staging_gateway or production_gateway
# See: https://github.com/3scale-qe/3scale-tests/blob/v2.16.0.8/testsuite/tests/apicast/policy/retry_policy/conftest.py#L20
@pytest.fixture(scope="module")
def staging_gateway(request, testconfig):
    """Deploy self-managed template based apicast gateway."""
    gw = gateway(kind=TemplateApicast, staging=True, name=blame(request, "gw"))
    if not testconfig["skip_cleanup"]:
        request.addfinalizer(gw.destroy)
    gw.create()

    return gw

###############################################################################
# To skip apicast retrying on 404 status code
# See: https://github.com/3scale-qe/3scale-tests/blob/v2.16.0.8/testsuite/tests/apicast/apiap/test_apiap_routing_to_backend.py#L71
def test_skip_apicast_retrying_on_404(application, api_client):

    # 3scale is slow, have one request with retry is often (but not everytime)
    # desirable to ensure all is already up
    application.test_request()

    client = api_client(disable_retry_status_list={404})

    assert client.get("/status/404").status_code == 404
