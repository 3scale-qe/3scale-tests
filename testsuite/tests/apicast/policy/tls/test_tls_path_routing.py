"""Test for TLS Apicast with path routing and logging"""

from urllib.parse import urlsplit

import pytest
import requests
from packaging.version import Version  # noqa # pylint: disable=unused-import

from testsuite import rawobj, TESTED_VERSION, APICAST_OPERATOR_VERSION  # noqa # pylint: disable=unused-import
from testsuite.capabilities import Capability
from testsuite.echoed_request import EchoedRequest
from testsuite.tests.apicast.policy.tls import embedded
from testsuite.utils import blame

pytestmark = [
    pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY, Capability.CUSTOM_ENVIRONMENT),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-8000"),
    pytest.mark.issue("https://issues.redhat.com/browse/THREESCALE-8252"),
    pytest.mark.skipif("TESTED_VERSION < Version('2.12')"),
    pytest.mark.skipif("APICAST_OPERATOR_VERSION < Version('0.6.0')"),
]


@pytest.fixture(scope="module")
def tls_policy(certificate):
    """Sets up the embedded TLS termination policy"""
    return rawobj.PolicyConfig(
        "tls",
        {
            "certificates": [
                {
                    "certificate": embedded(certificate.certificate, "tls.crt", "pkix-cert"),
                    "certificate_key": embedded(certificate.key, "tls.key", "x-iwork-keynote-sffkey"),
                }
            ]
        },
    )


@pytest.fixture(scope="module")
def logging_policy():
    """Sets up the logging policy"""
    return rawobj.PolicyConfig(
        "logging", {"custom_logging": "MY REQUEST HOST: {{original_request.host}} AND PATH: {{original_request.path}}"}
    )


def delete_all_mapping_rules(proxy):
    """Deletes all mapping rules in a given proxy."""
    mapping_rules = proxy.mapping_rules.list()
    for mapping_rule in mapping_rules:
        mapping_rule.delete()


@pytest.fixture(scope="module")
def backend_default(private_base_url, custom_backend):
    """
    Default backend with url from private_base_url.
    Change api_backend to echo-api for service2.
    """
    return custom_backend("backend_default", endpoint=f"{private_base_url('echo_api')}/service1")


@pytest.fixture(scope="module")
def service_mapping():
    """Change mapping rule for service"""
    return "/foo/bar"


@pytest.fixture(scope="module")
def service(service, service_mapping, tls_policy, logging_policy):
    """Delete mapping rules and add new one from/to default service."""
    proxy = service.proxy.list()
    metric = service.metrics.list()[0]
    proxy.policies.append(tls_policy)
    proxy.policies.append(logging_policy)
    delete_all_mapping_rules(proxy)

    proxy.mapping_rules.create(rawobj.Mapping(metric, service_mapping))
    proxy.update()

    return service


@pytest.fixture(scope="module")
def service2_mapping():
    """Change mapping rule for service2"""
    return "/bar/foo"


@pytest.fixture(scope="module")
def backend_default2(private_base_url, custom_backend):
    """
    Default backend with url from private_base_url.
    Change api_backend to echo-api for service2.
    """
    return custom_backend("backend_default", endpoint=f"{private_base_url('echo_api')}/service2")


@pytest.fixture(scope="module")
def backends_mapping2(backend_default2):
    """
    Due to the new 3Scale feature, we need to be able to create  custom backends and backend usages and then pass them
    to creation of custom service. By default, it does nothing, just lets you skip creating a backend in test files.
    """
    return {"/": backend_default2}


# pylint: disable=too-many-arguments
@pytest.fixture(scope="module")
def service2(request, custom_service, lifecycle_hooks, service2_mapping, tls_policy, logging_policy, backends_mapping2):
    """Create second service and mapping rule."""
    service2 = custom_service({"name": blame(request, "svc")}, backends=backends_mapping2, hooks=lifecycle_hooks)

    service2.proxy.list().policies.append(tls_policy)
    service2.proxy.list().policies.append(logging_policy)

    metric = service2.metrics.list()[0]
    proxy = service2.proxy.list()

    delete_all_mapping_rules(proxy)
    proxy.mapping_rules.create(rawobj.Mapping(metric, service2_mapping))
    proxy.update()

    return service2


@pytest.fixture(scope="module")
def application2(request, service2, custom_app_plan, custom_application, lifecycle_hooks):
    """Create custom application for service2."""
    plan = custom_app_plan(rawobj.ApplicationPlan(blame(request, "aplan")), service2)
    return custom_application(rawobj.Application(blame(request, "app"), plan), hooks=lifecycle_hooks)


@pytest.fixture(scope="module")
def client(api_client):
    """Client for the first application."""
    return api_client()


@pytest.fixture(scope="module")
def client2(application2, api_client):
    """Client for second application."""
    return api_client(application2)


@pytest.fixture(scope="module")
def gateway_options(gateway_options):
    """Deploy template apicast staging gateway."""
    gateway_options["path_routing"] = True

    return gateway_options


@pytest.fixture(scope="module")
def gateway_environment(gateway_environment):
    """Enables path routing on gateway"""
    gateway_environment.update({"APICAST_PATH_ROUTING": True})
    return gateway_environment


# pylint: disable=protected-access
def test_tls_path_routing_with_logging(client, client2, staging_gateway):
    """
    Preparation:
        - Creates TLS Apicast with enabled path routing
        - Creates 2 services
    Test:
        - Make request to path `/foo/bar`
        - Assert that it was routed to the right service
        - Make request to path `/bar/foo`
        - Assert that it was routed to the right service
        - Assert that logs contain the log in the correct date format
    """

    url1 = f'{client._base_url}/foo/bar?user_key={client.auth.credentials["user_key"]}'
    url2 = f'{client2._base_url}/bar/foo?user_key={client2.auth.credentials["user_key"]}'
    session = requests.Session()
    for _ in range(5):
        response = session.get(url1, verify=False)
        assert response.status_code == 200
        echoed_request = EchoedRequest.create(response)
        assert echoed_request.json["path"] == "/service1/foo/bar"
        response = session.get(url2, verify=False)
        assert response.status_code == 200
        echoed_request = EchoedRequest.create(response)
        assert echoed_request.json["path"] == "/service2/bar/foo"

    logs = staging_gateway.get_logs()
    assert f"MY REQUEST HOST: {urlsplit(client._base_url).hostname} AND PATH: /bar/foo" in logs
    assert f"MY REQUEST HOST: {urlsplit(client2._base_url).hostname} AND PATH: /foo/bar" in logs
