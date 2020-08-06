"""Test for TLS Termination Policy."""
import base64

import pytest
import requests

from testsuite.gateways.gateways import Capability
from testsuite.utils import randomize, blame
from testsuite import rawobj

pytestmark = [pytest.mark.flaky, pytest.mark.required_capabilities(Capability.STANDARD_GATEWAY)]


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
def ssl_certificate(staging_gateway):
    """Create ssl certificate for tls termination policy."""
    return staging_gateway.ssl_certificate.create("termination")


@pytest.fixture(scope="module")
def ssl_certificate_and_path(staging_gateway):
    """Returns paths for cert and key to be sent to apicast."""
    certificate = staging_gateway.ssl_certificate.get("termination")
    return (certificate.certificate_path, certificate.key_path)


@pytest.fixture(scope="module")
def mount_path(request):
    """Returns a path to be mounted on gateway."""
    return f'/var/run/secrets/{blame(request, "tls-term")}'


@pytest.fixture(scope="module")
def setup_gateway(request, staging_gateway, mount_path, ssl_certificate):
    """Mount volume from TLS secret on staging gateway."""
    cert, key = ssl_certificate.certificate, ssl_certificate.key

    secret_name = blame(request, "tls-term")
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
def tls_termination_policy_path_type(setup_gateway, mount_path):
    """Returns tls termination policy path type schema."""
    config = dict(certificate=f"{mount_path}/tls.crt",
                  certificate_key=f"{mount_path}/tls.key")
    return rawobj.PolicyConfig("tls", {"certificates": [config]})


@pytest.fixture(scope="module")
def tls_termination_policy_embedded_type(ssl_certificate):
    """Returns tls termination policy embedded type schema."""
    cert = get_embedded_data(ssl_certificate.certificate, "tls.crt", "pkix-cert")
    key = get_embedded_data(ssl_certificate.key, "tls.key", "x-iwork-keynote-sffkey")
    config = dict(certficate=cert, certificate_key=key)
    return rawobj.PolicyConfig("tls", {"certificates": [config]})


@pytest.fixture(scope="module")
def service(service, tls_termination_policy_path_type):
    """Service configured with path type tls termination policy."""
    service.proxy.list().policies.append(tls_termination_policy_path_type)
    return service


@pytest.fixture(scope="module")
def service2(request, service_proxy_settings, custom_service, lifecycle_hooks, tls_termination_policy_embedded_type):
    """Second service will be used for embedded type policy."""
    svc = custom_service({"name": blame(request, "service")}, service_proxy_settings, hooks=lifecycle_hooks)
    svc.proxy.list().policies.append(tls_termination_policy_embedded_type)
    return svc


@pytest.fixture(scope="module")
def application2(service2, custom_app_plan, custom_application, lifecycle_hooks):
    """First application bound to the account and service2."""
    plan = custom_app_plan(rawobj.ApplicationPlan(randomize("AppPlan")), service2)
    return custom_application(rawobj.Application(randomize("App"), plan), hooks=lifecycle_hooks)


def get_client(application):
    """Returns HttpClient instance with retrying feature skipped."""
    session = requests.Session()
    session.auth = application.authobj
    return application.api_client(session=session)


def test_path_type_policy_should_return_ok(application, ssl_certificate_and_path):
    """Test tls termination policy with path type configuration."""
    client = get_client(application)
    assert client.get("/get", cert=ssl_certificate_and_path).status_code == 200


def test_embedded_type_policy_should_return_ok(application2, ssl_certificate_and_path):
    """Test tls termination policy with embedded type configuration."""
    client = get_client(application2)
    assert client.get("/get", cert=ssl_certificate_and_path).status_code == 200
