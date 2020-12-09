"""Test Upstream Mutual TLS

Certificate and key added to the policy will be sent to upstream apis
which will make sure they're valid.
"""
import base64
from urllib.parse import urlparse

import pytest

from testsuite import rawobj
from testsuite.echoed_request import EchoedRequest
from testsuite.gateways import TemplateApicastOptions, TemplateApicast
from testsuite.utils import randomize, blame

pytestmark = pytest.mark.flaky


def get_embedded_data(pem: str, name: str, app: str) -> str:
    """Returns pem formatted for embedded configuration."""
    b64_pem = base64.b64encode(bytes(pem, "ascii")).decode('ascii')
    data = [
        f"data:application/{app}",
        f"name={name}",
        f"base64,{b64_pem}"
    ]
    return ";".join(data)


@pytest.fixture(scope="module")
def staging_gateway(request, configuration):
    """Deploy template apicast gateway."""
    settings_block = {
        "deployments": {
            "staging": blame(request, "upstream-mtls"),
            "production": blame(request, "upstream-mtls")
        },
    }
    options = TemplateApicastOptions(staging=True, settings_block=settings_block, configuration=configuration)
    gateway = TemplateApicast(requirements=options)

    request.addfinalizer(gateway.destroy)
    gateway.create()

    return gateway


@pytest.fixture(scope="module")
def mount_path(request):
    """Returns a path to be mounted on gateway."""
    return f'/var/run/secrets/{blame(request, "mtls")}'


@pytest.fixture(scope="module")
def setup_gateway(request, staging_gateway, mount_path, mtls_cert_and_key):
    """Mount volume from TLS secret on staging gateway."""
    cert, key = mtls_cert_and_key

    secret_name = blame(request, "mtls")
    resource = {
        "kind": "Secret",
        "apiVersion": "v1",
        "metadata": {
            "name": secret_name,
        },
        "data": {
            "tls.crt": base64.b64encode(cert.encode("ascii")).decode("ascii"),
            "tls.key": base64.b64encode(key.encode("ascii")).decode("ascii"),
        }
    }

    def turn_down():
        staging_gateway.openshift.delete("secret", secret_name)

    request.addfinalizer(turn_down)

    staging_gateway.openshift.apply(resource)
    staging_gateway.openshift.add_volume(staging_gateway.deployment, secret_name,
                                         mount_path, secret_name)


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def path_type_policy(mount_path, setup_gateway):
    """Returns upstream mtls policy configuration path type."""
    cert, key = f'{mount_path}/tls.crt', f'{mount_path}/tls.key'
    return rawobj.PolicyConfig("upstream_mtls", {"certificate_type": "path",
                                                 "certificate_key_type": "path",
                                                 "certificate": cert,
                                                 "certificate_key": key})


@pytest.fixture(scope="module")
def embedded_type_policy():
    """Returns a function for creating embedded type policy configuration."""

    def create(cert, key):
        embedded_cert = get_embedded_data(cert, "tls.crt", "pkix-cert")
        embedded_key = get_embedded_data(key, "tls.key", "x-iwork-keynote-sffkey")
        return rawobj.PolicyConfig("upstream_mtls", {"certificate_type": "embedded",
                                                     "certificate_key_type": "embedded",
                                                     "certificate": embedded_cert,
                                                     "certificate_key": embedded_key})
    return create


@pytest.fixture(scope="module")
def ssl_certificate_hostname(private_base_url):
    """Returns hostname to be used on ssl certificate creation."""
    return urlparse(private_base_url("httpbin_go_mtls")).hostname


@pytest.fixture(scope="module")
def service_proxy_settings(private_base_url):
    """Returns proxy data for mtls backend."""
    return rawobj.Proxy(private_base_url("httpbin_go_mtls"))


# pylint: disable=too-many-arguments,unused-argument
@pytest.fixture(scope="module")
def service(service, path_type_policy):
    """Service with upstream mtls path type policy."""
    service.proxy.list().policies.append(path_type_policy)
    return service


@pytest.fixture(scope="module")
def service2(request, service_proxy_settings, custom_service, lifecycle_hooks, embedded_type_policy,
             mtls_cert_and_key):
    """Second service with upstream mtls embedded type policy."""
    svc = custom_service({"name": blame(request, "svc")}, service_proxy_settings, hooks=lifecycle_hooks)
    svc.proxy.list().policies.append(embedded_type_policy(*mtls_cert_and_key))
    return svc


@pytest.fixture(scope="module")
def application2(service2, custom_app_plan, custom_application, lifecycle_hooks):
    """Second application bound to service2."""
    plan = custom_app_plan(rawobj.ApplicationPlan(randomize("AppPlan")), service2)
    return custom_application(rawobj.Application(randomize("App"), plan), hooks=lifecycle_hooks)


@pytest.fixture(scope="module")
def service3(request, service_proxy_settings, custom_service, lifecycle_hooks,
             ssl_certificate, embedded_type_policy):
    """Third service with upstream mtls policy and certs signed by unknown authority."""
    cert = ssl_certificate.create("unknown-authority")

    svc = custom_service({"name": blame(request, "svc")}, service_proxy_settings, hooks=lifecycle_hooks)
    svc.proxy.list().policies.append(embedded_type_policy(cert.certificate, cert.key))
    return svc


@pytest.fixture(scope="module")
def application3(service3, custom_app_plan, custom_application, lifecycle_hooks):
    """Third application bound to service3."""
    plan = custom_app_plan(rawobj.ApplicationPlan(randomize("AppPlan")), service3)
    return custom_application(rawobj.Application(randomize("App"), plan), hooks=lifecycle_hooks)


def test_upstream_mtls_path_type_policy(private_base_url, application):
    """Test upstream mtls for path type policy."""
    client = application.api_client()

    response = client.get("/get")
    assert response.status_code == 200

    echoed = EchoedRequest.create(response)
    assert echoed.headers["Host"].split(":")[0] == urlparse(private_base_url("httpbin_go_mtls")).hostname


def test_upstream_mtls_embedded_type_policy(private_base_url, application2):
    """Test upstream mtls for embedded type policy."""
    client = application2.api_client()

    response = client.get("/get")
    assert response.status_code == 200

    echoed = EchoedRequest.create(response)
    assert echoed.headers["Host"].split(":")[0] == urlparse(private_base_url("httpbin_go_mtls")).hostname


def test_upstream_mtls_unknown_authority_cert(private_base_url, application3):
    """Test upstream mtls for policy configured with certs signed by unknown authority."""
    client = application3.api_client()

    response = client.get("/get")
    assert response.status_code == 502
