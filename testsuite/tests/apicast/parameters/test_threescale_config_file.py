"""Rewrite of spec/openshift_specs/gateway_config_file_spec.rb

Test apicast with configuration from config maps.
"""
import json

import pytest

from testsuite.capabilities import Capability
from testsuite import rawobj
from testsuite.utils import blame

pytestmark = pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT)


@pytest.fixture(scope="module")
def gateway_environment(gateway_environment):
    """Sets location of the 3scale config file"""
    gateway_environment.update({"THREESCALE_CONFIG_FILE": "/opt/config/apicast_config"})
    return gateway_environment


def get_apicast_config(service):
    """Returns sandbox proxy configuration.

    Apicast configuration should be in the format:
    {
        "apicast_config": {
            "services": [{ `service_settings` }]
        }
    }
    """
    proxy = service.proxy.list()
    latest_config_version = proxy.configs.list(env="sandbox")[0]["proxy_config"]

    # make sure we're working with version 1
    assert latest_config_version["version"] == 1

    service_settings = latest_config_version["content"]

    return {"apicast_config": json.dumps({"services": [service_settings]})}


def setup_apicast_configuration(service, staging_gateway, configmap_name):
    """Configure apicast for reading configuration from ConfigMap."""
    staging_gateway.openshift.config_maps.add(configmap_name, get_apicast_config(service))
    staging_gateway.openshift.add_volume(staging_gateway.deployment, "apicast-config-vol",
                                         "/opt/config", configmap_name=configmap_name)


@pytest.fixture(scope="module")
def service(request, service, staging_gateway):
    """Set this service's configuration as the only configuration available on apicast.

    It's possible by setting `THREESCALE_CONFIG_FILE`. Requests to other services
    should not work and also return 404.
    """
    configmap_name = blame(request, "cm")

    setup_apicast_configuration(service, staging_gateway, configmap_name)

    yield service

    del staging_gateway.openshift.config_maps[configmap_name]


@pytest.fixture(scope="module")
def service2(request, service_proxy_settings, custom_service, lifecycle_hooks):
    """Create service2 whose configuration will not be set to apicast."""
    return custom_service({"name": blame(request, "svc")}, service_proxy_settings, hooks=lifecycle_hooks)


@pytest.fixture(scope="module")
def application2(service2, custom_app_plan, custom_application, request, lifecycle_hooks):
    """Create custom application for service2."""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service2)
    return custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)


# apicast setup happens in service fixture == setup is not global,
# tests/asserts have order dependency -> must be in one test because of
# parallel or single test run
def test_threescale_config_file_param(api_client, application2):
    """Call to /get mappend on service returns 200.

    service configuration is available for apicast.

    Call to /get on service2 returns 404.

    service2 configuration is not available for apicast.
    """
    assert api_client().get("/get").status_code == 200

    client = api_client(application2, disable_retry_status_list={404})

    assert client.get("/get").status_code == 404
