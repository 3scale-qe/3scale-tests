"""
This is complication of examples how to use testsuite and write tests. As such
this is not supposed to be executed and it isn't goal to have this executable
"""
from testsuite.gateways import SelfManagedApicastOptions, SelfManagedApicast, TemplateApicastOptions, TemplateApicast
from testsuite.capabilities import Capability
from testsuite.rhsso.rhsso import OIDCClientAuth
from threescale_api.resources import Service
import pytest
import rawobj
import requests


################################################################################
# run simple test
def test_basic_request(application):
    """test request has to pass and return HTTP 200"""
    assert application.test_request().status_code == 200
    assert application.test_request("/anything").status_code == 200


# or use api_client
def test_another_basic_request(api_client):
    """test requests have to pass and return HTTP 200"""
    client = api_client()
    assert client.get("/get").status_code == 200
    assert client.get("/get", params={"arg": "value"})
    assert client.post("/post", data={"arg": "value"}, headers={"X-Custom-Header": "value"})


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
# To test call against production gateway you can use the prod_client fixture which promotes the configuration to
# production and then creates the actual client
# (default value of the version is 1)

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


@pytest.mark.disruptive  # test should be mark as disruptive because of production gateway redeploy
@pytest.mark.required_capabilities(Capability.PRODUCTION_GATEWAY)  # Test should have mark that states that it needs production_gateway
def test_production_call_without_redeploy(application, prod_client):
    client = prod_client(application, redeploy=False)
    response = client.get("/get")

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


###############################################################################
# To explicitly specify gateway for tests override staging_gateway or production_gateway
@pytest.fixture(scope="session")
def staging_gateway(request, configuration):
    # Here you specify the same configuration in dict form as in the settings.yaml
    setting_block = {
        "deployments": {  # DeploymentConfigs
            "staging": "selfmanaged-staging",
            "production": "selfmanaged-production"
        }
    }
    options = TemplateApicastOptions(staging=True, settings_block=setting_block, configuration=configuration)
    gateway = TemplateApicast(requirements=options)

    request.addfinalizer(gateway.destroy)
    gateway.create()

    return gateway


###############################################################################
# To explicitly specify the gateway endpoints for the staging and production gateway

@pytest.fixture(scope="session")
def staging_gateway(settings_block, request, configuration):
    """Settings block with http(s) endpoints"""
    endpoints = {
        "endpoints": {
            "staging": "https://staging.custom.endpoint",
            "production": "https://production.custom.endpoint"
        }}
    settings_block.update(endpoints)

    options = TemplateApicastOptions(staging=True, settings_block=settings_block, configuration=configuration)
    gateway = TemplateApicast(requirements=options)

    request.addfinalizer(gateway.destroy)
    gateway.create()

    return settings_block


###############################################################################
# To skip apicast retrying on 404 status code
def test_skip_apicast_retrying_on_404(application, api_client):

    # 3scale is slow, have one request with retry is often (but not everytime)
    # desirable to ensure all is already up
    application.test_request()

    client = api_client(disable_retry_status_list={404})

    assert client.get("/status/404").status_code == 404


################################################################################
# Example usage of DockerRuntime
def example_docker():
    from testsuite.containers.docker_runtime import DockerRuntime
    from testsuite.containers.container_runtime import ContainerConfig
    from contextlib import closing

    with closing(DockerRuntime("tcp://10.0.145.159:2376")) as d:
        cc = ContainerConfig("mysql", "latest", {"MYSQL_ROOT_PASSWORD": "root"}, {"3306": "33767"}, cmd=["ls", "-la"])
        cc.attach_volume("/root/dkr", "/mnt")
        c = d.run(cc)
        print(d.logs(c))

        # d.stop(c)
        d.delete_container(c)


###############################################################################
# Example usage of PodmanRuntime
def example_podman():
    from testsuite.containers.podman_runtime import PodmanRuntime
    from testsuite.containers.container_runtime import ContainerConfig
    from contextlib import closing

    with closing(PodmanRuntime("ssh://root@10.0.145.150/run/podman/io.podman")) as d:
        cc = ContainerConfig("mysql", "latest", {"MYSQL_ROOT_PASSWORD": "root"}, {"3306": "33075"}, cmd=["ls"])
        cc.attach_volume("/root/blah", "/mnt")
        c = d.run(cc)
        print(d.logs(c))
        # d.stop(c)
        d.delete_container(c)


###############################################################################
# Example usage of DockerRuntime
def example_docker_no_cm():
    from testsuite.containers.docker_runtime import DockerRuntime
    from testsuite.containers.container_runtime import ContainerConfig

    d = DockerRuntime("tcp://10.0.145.159:2376")
    cc = ContainerConfig("mysql", "latest", {"MYSQL_ROOT_PASSWORD": "root"}, {"3306": "33767"}, cmd=["ls", "-la"])
    cc.attach_volume("/root/dkr", "/mnt")
    c = d.run(cc)
    print(d.logs(c))

    # d.stop(c)
    d.delete_container(c)
    d.close()


###############################################################################
# Example usage of PodmanRuntime
def example_podman_no_cm():
    from testsuite.containers.podman_runtime import PodmanRuntime
    from testsuite.containers.container_runtime import ContainerConfig

    d = PodmanRuntime("ssh://root@10.0.145.150/run/podman/io.podman")
    cc = ContainerConfig("mysql", "latest", {"MYSQL_ROOT_PASSWORD": "root"}, {"3306": "33076"}, cmd=["ls"])
    cc.attach_volume("/root/blah", "/mnt")
    c = d.run(cc)
    print(d.logs(c))
    # d.stop(c)
    d.delete_container(c)

    d.close()
