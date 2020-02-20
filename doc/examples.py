"""
This is complication of examples how to use testsuite and write tests. As such
this is not supposed to be executed and it isn't goal to have this executable
"""

from testsuite.rhsso.rhsso import OIDCClientAuth
from threescale_api.resources import Service
import pytest
import rawobj


################################################################################
# run simple test
def test_basic_request(application):
    """test request has to pass and return HTTP 200"""
    assert application.test_request().status_code == 200
    assert application.test_request("/anything").status_code == 200


# or use api_client
def test_another_basic_request(api_client):
    """test requests have to pass and return HTTP 200"""
    assert api_client.get("/get").status_code == 200
    assert api_client.get("/get", params={"arg": "value"})
    assert api_client.post("/post", data={"arg": "value"}, headers={"X-Custom-Header": "value"})


################################################################################
# to add policy use policy_settings fixture.
# BEWARE! This is defined in testsuite/tests/apicast/policy/conftest.py
@pytest.fixture(scope="module")
def policy_settings():
    """Have service with upstream_connection policy added to the chain and
    configured to read_timeout after 5 seconds"""
    return rawobj.PolicyConfig("upstream_connection", {"read_timeout": 5})


################################################################################
# To switch authentication define two following fixtures
@pytest.fixture(scope="module")
def service_settings(service_settings):
    """Have service with app_id/app_key pair authentication"""
    service_settings.update({"backend_version": Service.AUTH_APP_ID_KEY})
    return service_settings


@pytest.fixture(scope="module")
def service_proxy_settings(service_proxy_settings):
    """Expect credentials to be passed in headers"""
    service_proxy_settings.update({"credentials_location": "headers"})
    return service_proxy_settings
    
    
###############################################################################
# To call using production gateway define following fixture
# (default value of the version is 1)
@pytest.fixture
def prod_client(application, testconfig, redeploy_production_gateway):
    """api_client using production gateway"""
    application.service.proxy.list().promote(version='foo_version')
    redeploy_production_gateway()
    return application.api_client(endpoint="endpoint", verify=testconfig["ssl_verify"])


# and then make requests using this fixture
@pytest.mark.disruptive  # test should be mark as disruptive because of production gateway redeploy
def test_production_call(prod_client):
    response = prod_client.get("/get")


###############################################################################
# When requiring compatible backend to be used define following fixture
@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url):
    return rawobj.Proxy(private_base_url("echo_api"))


###############################################################################
# To configure metrics mapping rules, insert following into the service fixture
@pytest.fixture(scope="module")
def service(service):
    proxy = service.proxy.list()

    metric = service.metrics.create(rawobj.Metric("name_foo"))
    proxy.mapping_rules.create(rawobj.Mapping(metric, pattern="/foo"))

    # proxy needs to be updated to apply added mapping
    proxy.update()
    return service
